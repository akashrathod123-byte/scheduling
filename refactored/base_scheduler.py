"""
Base Scheduler - Abstract class for all department schedulers
Provides common functionality to eliminate duplication
"""

import pandas as pd
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Tuple
from data_loader import DataLoader
from rotation_engine import RotationEngine


class BaseScheduler(ABC):
    """
    Abstract base class for department schedulers

    Provides:
    - Data loading
    - PTO filtering
    - Rotation engine access
    - Common assignment patterns
    """

    def __init__(self, target_date: datetime, data_loader: DataLoader):
        self.target_date = target_date
        self.data_loader = data_loader
        self.department = self.get_department_name()

        # Load data
        self.forecast_df = data_loader.load_forecast()
        self.historical_df = self.load_historical_data()
        self.rotation_engine = RotationEngine(self.historical_df, target_date)

        # Get employees
        self.all_employees_df = data_loader.get_employees_by_department(self.department)
        self.all_employees_df = data_loader.check_pto(self.all_employees_df)

        # Filter available
        self.available_df = self.all_employees_df[
            ~self.all_employees_df['Is_Full_Day_PTO']
        ].copy()

        self.pto_summary_df = self.all_employees_df[
            self.all_employees_df['Is_Full_Day_PTO']
        ].copy()

    # ========================================================================
    # ABSTRACT METHODS - Must be implemented by subclasses
    # ========================================================================

    @abstractmethod
    def get_department_name(self) -> str:
        """Return department name (e.g., 'Bin Filling', 'Small Packing')"""
        pass

    @abstractmethod
    def load_historical_data(self) -> pd.DataFrame:
        """Load department-specific historical data"""
        pass

    @abstractmethod
    def calculate_needs(self) -> pd.DataFrame:
        """Calculate FTE/position needs from forecast"""
        pass

    @abstractmethod
    def assign_employees(self) -> pd.DataFrame:
        """Main assignment logic"""
        pass

    # ========================================================================
    # MAIN SCHEDULING WORKFLOW
    # ========================================================================

    def schedule(self) -> Dict[str, pd.DataFrame]:
        """
        Main scheduling workflow

        Returns dict with:
        - 'assignments': Main assignment dataframe
        - 'needs': FTE/position needs
        - 'pto_summary': Employees on PTO
        - 'special_roles': Special assignments (if applicable)
        """
        self.print_header()

        # Calculate needs
        needs_df = self.calculate_needs()

        # Print employee pool summary
        self.print_employee_summary()

        # Assign employees
        assignments_df = self.assign_employees()

        # Print final summary
        self.print_final_summary(assignments_df)

        return {
            'assignments': assignments_df,
            'needs': needs_df,
            'pto_summary': self.pto_summary_df,
        }

    # ========================================================================
    # COMMON UTILITIES
    # ========================================================================

    def get_forecast_value(self, column_name: str) -> float:
        """Get forecast value for target date"""
        forecast_row = self.forecast_df[self.forecast_df['Date'] == self.target_date]
        if forecast_row.empty:
            raise ValueError(f"No forecast found for {self.target_date}")
        return forecast_row[column_name].values[0]

    def filter_by_shift(self, shift_key: str) -> pd.DataFrame:
        """Filter available employees by shift"""
        return self.available_df[self.available_df['Shift_Key'] == shift_key].copy()

    def check_eligibility(self, employee_row: pd.Series, eligibility_field: str) -> bool:
        """Check if employee has required cross-training"""
        return employee_row.get(eligibility_field, False) == True

    # ========================================================================
    # PRINTING
    # ========================================================================

    def print_header(self):
        """Print department header"""
        print("\n" + "="*80)
        print(f"{self.department.upper()} SCHEDULE")
        print("="*80)

    def print_employee_summary(self):
        """Print employee pool summary"""
        print(f"\n=== {self.department} Employee Pool ===")
        print(f"Total employees: {len(self.all_employees_df)}")
        print(f"Full-day PTO: {len(self.pto_summary_df)}")
        print(f"Available: {len(self.available_df)}")

        # Print shift breakdown
        if 'Shift_Key' in self.available_df.columns:
            print(f"\nBy Shift:")
            shift_counts = self.available_df['Shift_Key'].value_counts().sort_index()
            for shift, count in shift_counts.items():
                print(f"  {shift}: {count}")

    def print_final_summary(self, assignments_df: pd.DataFrame):
        """Print final assignment summary"""
        print(f"\n{'='*80}")
        print(f"{self.department.upper()} SUMMARY")
        print(f"{'='*80}")

        if assignments_df.empty:
            print("No assignments")
            return

        total = len(assignments_df)
        assigned = len(assignments_df[assignments_df['Status'] == 'Assigned'])
        extra = len(assignments_df[assignments_df['Status'] == 'Extra'])
        unfilled = len(assignments_df[assignments_df['Employee'].isna()])

        print(f"Total: {total}")
        print(f"Assigned: {assigned}")
        if extra > 0:
            print(f"Extra: {extra}")
        if unfilled > 0:
            print(f"⚠️  Unfilled: {unfilled}")

    # ========================================================================
    # COMMON ASSIGNMENT PATTERNS
    # ========================================================================

    def assign_by_shift_and_columns(
        self,
        template_df: pd.DataFrame,
        special_columns: Dict[str, set] = None
    ) -> pd.DataFrame:
        """
        Generic column-based assignment (for Packing, Shipping, Will Call)

        Args:
            template_df: Template with Shift, Columns, Num_Stations
            special_columns: Dict of special requirements (e.g., {'forklift': {3, 5}})

        Returns:
            Assignments dataframe
        """
        all_assignments = []

        for _, template_row in template_df.iterrows():
            shift_key = template_row['Shift']
            shift_columns = template_row['Columns']
            num_needed = int(template_row['Num_Stations'])

            shift_employees = self.filter_by_shift(shift_key)

            if shift_employees.empty:
                # Add unfilled positions
                for _ in range(num_needed):
                    all_assignments.append({
                        'Employee': None,
                        'Shift': shift_key,
                        'Column': None,
                        'Status': 'NEED CONFIRMATION'
                    })
                continue

            # Define eligibility function
            def is_eligible(emp_name: str, column: int) -> bool:
                if not special_columns:
                    return True

                emp_row = shift_employees[shift_employees['Employee'] == emp_name].iloc[0]

                # Check special requirements
                for role, cols in special_columns.items():
                    if column in cols:
                        field = f"{role.title().replace('_', '')}"
                        if not emp_row.get(field, False):
                            return False

                return True

            # Define cost function
            def calc_cost(emp_name: str, column: int) -> float:
                return self.rotation_engine.column_rotation_cost(
                    emp_name, column, shift_columns
                )

            # Optimal assignment
            assignments = self.rotation_engine.optimal_assign(
                employees=shift_employees['Employee'].tolist(),
                positions=shift_columns,
                eligibility_func=is_eligible,
                cost_func=calc_cost,
                num_needed=num_needed
            )

            # Build assignment records
            for emp, col, cost in assignments:
                all_assignments.append({
                    'Employee': emp,
                    'Shift': shift_key,
                    'Column': col,
                    'Status': 'Assigned'
                })

            # Add unfilled if needed
            if len(assignments) < num_needed:
                for _ in range(num_needed - len(assignments)):
                    all_assignments.append({
                        'Employee': None,
                        'Shift': shift_key,
                        'Column': None,
                        'Status': 'NEED CONFIRMATION'
                    })

        return pd.DataFrame(all_assignments)
