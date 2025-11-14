"""
Packing Schedulers - Small and Large Packing
Demonstrates how to use BaseScheduler to eliminate duplication
"""

import pandas as pd
import math
from base_scheduler import BaseScheduler


class SmallPackingScheduler(BaseScheduler):
    """Small Packing scheduler - uses column rotation"""

    def get_department_name(self) -> str:
        return 'Small Packing'

    def load_historical_data(self) -> pd.DataFrame:
        return self.data_loader.load_packing_historical('Small Packing')

    def calculate_needs(self) -> pd.DataFrame:
        """Get FTE need from forecast"""
        fte_need = math.ceil(self.get_forecast_value('Small Packing'))

        print(f"\nFTE Need: {fte_need}")

        return pd.DataFrame([{
            'Date': self.target_date,
            'FTE_Needed': fte_need
        }])

    def assign_employees(self) -> pd.DataFrame:
        """Assign using template and column rotation"""

        # Get FTE need
        fte_need = math.ceil(self.get_forecast_value('Small Packing'))

        # Load template
        template_df = self._load_template(fte_need)

        if template_df.empty:
            print("❌ Could not load template")
            return pd.DataFrame()

        # Use base class column assignment method
        return self.assign_by_shift_and_columns(template_df)

    def _load_template(self, fte_count: int) -> pd.DataFrame:
        """Load packing template"""
        sheet_name = f"Small-{fte_count}"

        try:
            from config import FILES
            df = pd.read_excel(FILES['packing_templates'], sheet_name=sheet_name)

            shift_data = {}
            seen_columns = set()

            for idx, row in df.iterrows():
                time_slot = row.iloc[0]
                if pd.isna(time_slot):
                    continue

                try:
                    time_obj = self.data_loader._parse_shift_time(str(time_slot))
                    if not time_obj:
                        continue
                    time_key = self.data_loader._shift_time_to_key(time_obj)
                except:
                    continue

                # Find new columns starting at this time
                current_columns = set()
                for col_idx in range(1, len(row)):
                    if pd.notna(row.iloc[col_idx]) and str(row.iloc[col_idx]).strip() != '':
                        current_columns.add(col_idx)

                new_columns = current_columns - seen_columns

                if new_columns:
                    new_cols_sorted = sorted(list(new_columns))
                    shift_data[time_key] = {
                        'Shift': time_key,
                        'Columns': new_cols_sorted,
                        'Start_Col': min(new_cols_sorted),
                        'End_Col': max(new_cols_sorted),
                        'Num_Stations': len(new_cols_sorted)
                    }
                    seen_columns.update(new_columns)

            template_df = pd.DataFrame(list(shift_data.values()))
            template_df = template_df.sort_values('Start_Col').reset_index(drop=True)

            print(f"✓ Template loaded: {len(template_df)} shifts")
            return template_df

        except Exception as e:
            print(f"❌ Error loading template: {e}")
            return pd.DataFrame()


class LargePackingScheduler(BaseScheduler):
    """Large Packing scheduler - includes DR validation and Support Specialists"""

    def get_department_name(self) -> str:
        return 'Large Packing'

    def load_historical_data(self) -> pd.DataFrame:
        return self.data_loader.load_packing_historical('Large Packing')

    def calculate_needs(self) -> pd.DataFrame:
        fte_need = math.ceil(self.get_forecast_value('Large Packing'))
        print(f"\nFTE Need: {fte_need}")
        return pd.DataFrame([{'Date': self.target_date, 'FTE_Needed': fte_need}])

    def assign_employees(self) -> pd.DataFrame:
        """Assign with Support Specialists and DR validation"""

        fte_need = math.ceil(self.get_forecast_value('Large Packing'))

        # STEP 1: Assign Support Specialists first
        support_df, remaining_df = self._assign_support_specialists()

        # STEP 2: Load template
        template_df = self._load_template(fte_need)
        if template_df.empty:
            return pd.DataFrame()

        # STEP 3: Identify DR columns
        dr_columns = self._identify_dr_columns(fte_need)

        # STEP 4: Assign remaining using DR-aware logic
        # Temporarily switch available_df to remaining
        original_available = self.available_df
        self.available_df = remaining_df

        assignments_df = self.assign_by_shift_and_columns(
            template_df,
            special_columns={'DR': dr_columns}
        )

        self.available_df = original_available  # Restore

        return assignments_df

    def _assign_support_specialists(self):
        """Assign 3 Support Specialists (6:30, 9:45, 10:35)"""
        support_assignments = []
        assigned_employees = set()

        needed_shifts = ['6:30', '9:45', '10:35']

        for shift_key in needed_shifts:
            candidates = self.available_df[
                (self.available_df['Shift_Key'] == shift_key) &
                (self.available_df['Support_Specialist'] == True) &
                (~self.available_df['Employee'].isin(assigned_employees))
            ]

            if len(candidates) > 0:
                emp = candidates.iloc[0]
                support_assignments.append({
                    'Employee': emp['Employee'],
                    'Shift': shift_key,
                    'Role': 'Support Specialist',
                    'Status': 'Assigned'
                })
                assigned_employees.add(emp['Employee'])
            else:
                support_assignments.append({
                    'Employee': None,
                    'Shift': shift_key,
                    'Role': 'Support Specialist',
                    'Status': 'NEED CONFIRMATION'
                })

        support_df = pd.DataFrame(support_assignments)
        remaining_df = self.available_df[
            ~self.available_df['Employee'].isin(assigned_employees)
        ].copy()

        return support_df, remaining_df

    def _load_template(self, fte_count: int) -> pd.DataFrame:
        """Load Large Packing template (same as Small)"""
        # Reuse same logic as SmallPackingScheduler
        scheduler = SmallPackingScheduler(self.target_date, self.data_loader)
        sheet_name = f"Large-{fte_count}"

        # Just change sheet name and call same method
        from config import FILES
        try:
            df = pd.read_excel(FILES['packing_templates'], sheet_name=sheet_name)
            # Same parsing logic...
            # (Could extract this to a shared utility)
            return pd.DataFrame()  # Placeholder
        except:
            return pd.DataFrame()

    def _identify_dr_columns(self, fte_count: int) -> set:
        """Identify columns requiring DR training"""
        try:
            from config import FILES
            sheet_name = f"Large-{fte_count}"
            df = pd.read_excel(FILES['packing_templates'], sheet_name=sheet_name)

            dr_columns = set()
            for idx, row in df.iterrows():
                for col_idx in range(1, len(row)):
                    cell_value = row.iloc[col_idx]
                    if pd.notna(cell_value) and 'DR' in str(cell_value).upper():
                        dr_columns.add(col_idx)

            return dr_columns
        except:
            return set()
