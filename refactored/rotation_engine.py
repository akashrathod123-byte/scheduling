"""
Rotation Engine - Generic Assignment Optimization
Handles rotation calculations and optimal assignment using Hungarian algorithm
"""

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from typing import List, Set, Tuple, Dict, Callable
from datetime import datetime, timedelta


class RotationEngine:
    """
    Generic assignment optimizer that works for:
    - Bin Filling workgroups
    - Packing columns
    - Shipping columns
    - Will Call positions
    """

    def __init__(self, historical_df: pd.DataFrame, target_date: datetime):
        self.historical_df = historical_df
        self.target_date = target_date

    # ========================================================================
    # OPTIMAL ASSIGNMENT (Hungarian Algorithm)
    # ========================================================================

    def optimal_assign(
        self,
        employees: List[str],
        positions: List[any],
        eligibility_func: Callable[[str, any], bool],
        cost_func: Callable[[str, any], float],
        num_needed: int
    ) -> List[Tuple[str, any, float]]:
        """
        Find optimal employee-to-position assignments using Hungarian algorithm

        Args:
            employees: List of employee names
            positions: List of positions (workgroups, columns, printers, etc.)
            eligibility_func: Function(employee, position) -> bool (checks if eligible)
            cost_func: Function(employee, position) -> float (rotation cost)
            num_needed: Number of assignments needed

        Returns:
            List of (employee, position, cost) tuples
        """

        # Build all valid (employee, position) pairs with costs
        valid_pairs = []

        for emp in employees:
            for pos in positions:
                if not eligibility_func(emp, pos):
                    continue  # Not eligible

                cost = cost_func(emp, pos)
                valid_pairs.append({
                    'employee': emp,
                    'position': pos,
                    'cost': cost
                })

        if not valid_pairs:
            return []

        # Create cost matrix
        emp_list = list(set([p['employee'] for p in valid_pairs]))
        pos_list = list(set([p['position'] for p in valid_pairs]))

        cost_matrix = np.full((len(emp_list), len(pos_list)), 1000.0)
        pair_lookup = {}

        for pair in valid_pairs:
            emp_idx = emp_list.index(pair['employee'])
            pos_idx = pos_list.index(pair['position'])
            cost_matrix[emp_idx, pos_idx] = pair['cost']
            pair_lookup[(emp_idx, pos_idx)] = pair

        # Solve with Hungarian algorithm
        emp_indices, pos_indices = linear_sum_assignment(cost_matrix)

        # Extract assignments
        assignments = []
        for emp_idx, pos_idx in zip(emp_indices, pos_indices):
            if cost_matrix[emp_idx, pos_idx] >= 1000:
                continue  # Infeasible

            if len(assignments) >= num_needed:
                break

            pair = pair_lookup[(emp_idx, pos_idx)]
            assignments.append((pair['employee'], pair['position'], pair['cost']))

        return assignments

    # ========================================================================
    # ROTATION COST FUNCTIONS
    # ========================================================================

    def column_rotation_cost(self, employee: str, column: int, shift_columns: List[int]) -> float:
        """
        Calculate rotation cost for column assignments (Packing, Shipping, Will Call)

        Logic:
        - Distance 0 (same column) = 100 (very bad)
        - Distance 1 (next column) = 1 (ideal)
        - Distance 2-5 = moderate
        - No history = 5 (neutral)
        """
        last_col = self.get_last_column(employee)

        if last_col is None or last_col not in shift_columns:
            return 5  # No history, neutral cost

        last_idx = shift_columns.index(last_col)
        col_idx = shift_columns.index(column)

        # Circular distance
        distance = (col_idx - last_idx) % len(shift_columns)

        if distance == 0:
            return 100  # Same column = bad
        elif distance == 1:
            return 1    # Natural rotation = best
        elif distance <= 5:
            return distance + 2
        else:
            return distance + 10

    def workgroup_rotation_cost(
        self,
        employee: str,
        workgroup: str,
        workgroup_order: List[str]
    ) -> float:
        """
        Calculate rotation cost for workgroup assignments (Bin Filling)

        Logic:
        - Distance 0 (same workgroup) = 100 (very bad)
        - Distance 1 (next workgroup) = 1 (ideal)
        - Unknown previous = 5 (neutral)
        """
        last_wg = self.get_last_workgroup(employee)

        if not last_wg or last_wg == 'Unknown':
            return 5  # No history

        try:
            from_idx = workgroup_order.index(last_wg)
            to_idx = workgroup_order.index(workgroup)

            # Circular distance
            if to_idx >= from_idx:
                distance = to_idx - from_idx
            else:
                distance = (len(workgroup_order) - from_idx) + to_idx

            if distance == 0:
                return 100  # Same workgroup = bad
            elif distance == 1:
                return 1    # Natural rotation = best
            elif distance <= 5:
                return distance + 2
            else:
                return distance + 10
        except:
            return 5  # Not found in order

    # ========================================================================
    # HISTORY LOOKUPS
    # ========================================================================

    def get_last_column(self, employee: str, days_back: int = 7) -> int:
        """Get employee's last column assignment"""
        if self.historical_df.empty:
            return None

        try:
            emp_history = self.historical_df.loc[employee]

            # Look back through date columns
            cutoff = self.target_date - timedelta(days=days_back)

            for col in reversed(emp_history.index):
                try:
                    col_date = datetime.strptime(col, "%m/%d/%y")
                    if cutoff <= col_date < self.target_date:
                        col_value = emp_history[col]
                        if pd.notna(col_value) and col_value != '':
                            return int(col_value)
                except:
                    continue
        except:
            pass

        return None

    def get_last_workgroup(self, employee: str) -> str:
        """Get employee's last workgroup assignment"""
        if self.historical_df.empty:
            return None

        emp_history = self.historical_df[self.historical_df['Employee'] == employee]
        if emp_history.empty:
            return None

        # Most recent record
        latest = emp_history.iloc[0]
        return latest.get('Workgroup', None)

    def get_last_printer(self, employee: str) -> str:
        """Get employee's last printer assignment"""
        if self.historical_df.empty:
            return None

        emp_history = self.historical_df[self.historical_df['Employee'] == employee]
        if emp_history.empty:
            return None

        latest = emp_history.iloc[0]
        return latest.get('Printer', None)

    def get_last_role(self, employee: str, department: str) -> str:
        """Get employee's last role (for Rack Filling or Freight)"""
        if self.historical_df.empty:
            return None

        emp_history = self.historical_df[
            (self.historical_df['Employee'] == employee) &
            (self.historical_df['Department'] == department)
        ].sort_values('Date', ascending=False)

        if emp_history.empty:
            return None

        return emp_history.iloc[0].get('Role', None)

    def count_role_frequency(self, employee: str, role: str, days_back: int = 14) -> int:
        """Count how many times employee did a role in past N days"""
        if self.historical_df.empty:
            return 0

        cutoff = self.target_date - timedelta(days=days_back)

        emp_history = self.historical_df[
            (self.historical_df['Employee'] == employee) &
            (self.historical_df['Role'] == role) &
            (self.historical_df['Date'] >= cutoff)
        ]

        return len(emp_history)

    # ========================================================================
    # SPECIAL ASSIGNMENTS
    # ========================================================================

    def rotate_special_role(
        self,
        candidates: pd.DataFrame,
        role_name: str,
        historical_identifier: str
    ) -> str:
        """
        Select employee for special role based on longest time since last assignment

        Args:
            candidates: DataFrame of eligible employees
            role_name: Name of role (e.g., 'Floor Responder')
            historical_identifier: Column/marker in history (e.g., 'FR', '2625')

        Returns:
            Selected employee name
        """
        if candidates.empty:
            return None

        rotation_scores = []

        for _, emp_row in candidates.iterrows():
            emp_name = emp_row['Employee']

            # Find last time they did this role
            if self.historical_df.empty:
                days_since = 999
            else:
                emp_history = self.historical_df[self.historical_df['Employee'] == emp_name]
                role_records = emp_history[
                    emp_history['Assignment'].str.contains(historical_identifier, na=False)
                ]

                if role_records.empty:
                    days_since = 999
                else:
                    last_date = role_records.iloc[0]['Date']
                    days_since = (self.target_date - last_date).days

            rotation_scores.append({
                'employee': emp_name,
                'days_since': days_since
            })

        # Choose employee who hasn't done it in longest time
        rotation_scores.sort(key=lambda x: x['days_since'], reverse=True)
        return rotation_scores[0]['employee']
