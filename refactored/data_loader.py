"""
Data Loader - Single Source of Truth
Handles all Excel file loading and parsing in one place
"""

import pandas as pd
from datetime import datetime, timedelta, time
from typing import Dict, Optional
from config import FILES, FULL_DAY_PTO_CODES, CT_COLUMNS


class DataLoader:
    """Centralized data loading with caching"""

    def __init__(self, target_date: datetime):
        self.target_date = target_date
        self._cache = {}

    def _load_sheet(self, file_key: str, sheet_name: str) -> pd.DataFrame:
        """Load Excel sheet with caching"""
        cache_key = f"{file_key}_{sheet_name}"
        if cache_key not in self._cache:
            self._cache[cache_key] = pd.read_excel(FILES[file_key], sheet_name=sheet_name)
        return self._cache[cache_key]

    # ========================================================================
    # CORE DATA LOADING
    # ========================================================================

    def load_forecast(self) -> pd.DataFrame:
        """Load forecast data"""
        return self._load_sheet('inputs', 'Forecast')

    def load_lookup_table(self, is_friday: bool = False) -> pd.DataFrame:
        """Load capacity lookup table"""
        sheet = 'Lookup F' if is_friday else 'Lookup M-T'
        return self._load_sheet('inputs', sheet)

    def load_work_distribution(self) -> pd.DataFrame:
        """Load work distribution percentages"""
        return self._load_sheet('inputs', 'Work Distribution')

    def load_pto(self) -> pd.DataFrame:
        """Load PTO data"""
        return self._load_sheet('inputs', 'PTO')

    def load_cross_training(self) -> pd.DataFrame:
        """Load cross training data"""
        return self._load_sheet('inputs', 'Cross Training')

    def load_freight_rotation(self) -> pd.DataFrame:
        """Load freight rotation schedule"""
        return self._load_sheet('inputs', 'Freight')

    def load_historical_staffing(self, days_back: int = 7) -> pd.DataFrame:
        """Load historical bin/rack filling assignments"""
        df = pd.read_excel(FILES['historical_staffing'], header=0)

        historical_records = []
        start_date = self.target_date - timedelta(days=days_back)

        employee_col = df.columns[0]
        dept_col = df.columns[1]

        for _, row in df.iterrows():
            emp_name = str(row[employee_col]).strip() if pd.notna(row[employee_col]) else None
            if not emp_name:
                continue

            dept = str(row[dept_col]).strip() if pd.notna(row[dept_col]) else ''

            for col in df.columns[2:]:
                try:
                    col_date = pd.to_datetime(col, errors='coerce')
                    if pd.isna(col_date) or not (start_date <= col_date < self.target_date):
                        continue

                    cell_value = row[col]
                    if pd.isna(cell_value):
                        continue

                    # Parse assignment (e.g., "A228:30" or "N05:15,H3:10")
                    historical_records.append({
                        'Date': col_date,
                        'Employee': emp_name,
                        'Department': dept,
                        'Assignment': str(cell_value).strip()
                    })
                except:
                    continue

        return pd.DataFrame(historical_records) if historical_records else pd.DataFrame()

    def load_packing_historical(self, dept: str) -> pd.DataFrame:
        """Load packing historical column assignments"""
        try:
            df = pd.read_excel(FILES['packing_historical'], index_col=0)
            return df[df['Department'] == dept].drop('Department', axis=1) if 'Department' in df.columns else df
        except:
            return pd.DataFrame()

    def load_warehouse_tasks(self, days_back: int = 30) -> pd.DataFrame:
        """Load warehouse task history"""
        try:
            df = pd.read_excel(FILES['warehouse_tasks'])
            df['Date'] = pd.to_datetime(df['Date'])
            cutoff = self.target_date - timedelta(days=days_back)
            return df[df['Date'] >= cutoff]
        except:
            return pd.DataFrame()

    # ========================================================================
    # EMPLOYEE EXTRACTION
    # ========================================================================

    def get_employees_by_department(self, department: str) -> pd.DataFrame:
        """
        Extract employees for a specific department from cross training

        Returns DataFrame with: Employee, Shift_Time, Shift_Key, and cross-training flags
        """
        ct_df = self.load_cross_training()
        employees = []

        for _, row in ct_df.iterrows():
            dept = str(row.get('Department', '')).strip()
            if dept != department:
                continue

            name = str(row.get('Employee Name', '')).strip()
            if not name:
                continue

            # Check CMT (only for Bin Filling)
            if department == 'Bin Filling':
                cmt = row.get('CMT', '')
                if pd.notna(cmt) and str(cmt).strip().upper() == 'X':
                    continue

            # Parse shift
            shift_time = self._parse_shift_time(row.get('Assigned Start Time', ''))
            if not shift_time:
                continue

            # Build employee record with cross-training
            emp_data = {
                'Employee': name,
                'Shift_Time': shift_time,
                'Shift_Key': self._shift_time_to_key(shift_time),
            }

            # Add department-specific cross-training flags
            emp_data.update(self._get_cross_training_flags(row, department))

            employees.append(emp_data)

        return pd.DataFrame(employees)

    def _get_cross_training_flags(self, row, department: str) -> dict:
        """Extract cross-training flags based on department"""
        flags = {}

        if department == 'Bin Filling':
            flags['Supplies_Eligible'] = self._has_training(row, CT_COLUMNS['bf_supplies'])
            flags['Replen_Eligible'] = self._has_training(row, CT_COLUMNS['bf_replen'])
            flags['Cuts_Eligible'] = self._has_training(row, CT_COLUMNS['bf_cuts'])
            flags['FR_Eligible'] = self._has_training(row, CT_COLUMNS['bf_fr'])

        elif department == 'Rack Filling':
            flags['OP_Eligible'] = self._has_training(row, CT_COLUMNS['rf_op'])
            flags['Cuts_Eligible'] = self._has_training(row, CT_COLUMNS['rf_cuts'])
            flags['Hinges_Eligible'] = self._has_training(row, CT_COLUMNS['rf_hinges'])
            flags['Tugger_Eligible'] = self._has_training(row, CT_COLUMNS['rf_tugger'])
            flags['Parcel_Eligible'] = self._has_training(row, CT_COLUMNS['rf_parcel'])
            flags['Replen_Eligible'] = self._has_training(row, CT_COLUMNS['rf_replen'])
            flags['Tubes_Eligible'] = self._has_training(row, CT_COLUMNS['rf_tubes'])
            flags['FR_Eligible'] = self._has_training(row, CT_COLUMNS['rf_fr'])

        elif department == 'Large Packing':
            flags['DR_Eligible'] = self._has_training(row, CT_COLUMNS['lp_dr'])
            flags['Support_Specialist'] = self._has_training(row, CT_COLUMNS['lp_support'])

        elif department == 'Parcel Shipping':
            flags['Forklift'] = self._has_training(row, CT_COLUMNS['ps_forklift'])
            flags['Additional_Handling'] = self._has_training(row, CT_COLUMNS['ps_additional_handling'])
            flags['Trash_Tugging'] = self._has_training(row, CT_COLUMNS['ps_trash_tugging'])
            flags['Barge_BLD'] = self._has_training(row, CT_COLUMNS['ps_barge_bld'])

        elif department == 'Will Call':
            flags['Counter_Eligible'] = self._has_training(row, CT_COLUMNS['wc_counter'])
            flags['Notes_Eligible'] = self._has_training(row, CT_COLUMNS['wc_notes'])

        return flags

    def _has_training(self, row, col_idx: int) -> bool:
        """Check if employee has cross-training (X in column)"""
        return pd.notna(row.iloc[col_idx]) and str(row.iloc[col_idx]).strip().upper() == 'X'

    # ========================================================================
    # PTO CHECKING
    # ========================================================================

    def check_pto(self, employees_df: pd.DataFrame) -> pd.DataFrame:
        """
        Add PTO columns to employee dataframe

        Returns df with: Is_Full_Day_PTO, PTO_Code columns added
        """
        pto_df = self.load_pto()

        # Find PTO column for target date
        pto_col = None
        for col in pto_df.columns:
            if col != 'Name':
                try:
                    col_date = pd.to_datetime(col).to_pydatetime().replace(hour=0, minute=0, second=0, microsecond=0)
                    if col_date.date() == self.target_date.date():
                        pto_col = col
                        break
                except:
                    continue

        if not pto_col:
            employees_df['Is_Full_Day_PTO'] = False
            employees_df['PTO_Code'] = ''
            return employees_df

        # Check PTO for each employee
        def check_employee_pto(name):
            try:
                emp_row = pto_df[pto_df['Name'] == name]
                if emp_row.empty:
                    return False, ""

                pto_code = emp_row[pto_col].values[0]
                if pd.isna(pto_code):
                    return False, ""

                pto_str = str(pto_code).strip()
                return pto_str in FULL_DAY_PTO_CODES, pto_str
            except:
                return False, ""

        pto_status = employees_df['Employee'].apply(check_employee_pto)
        employees_df['Is_Full_Day_PTO'] = pto_status.apply(lambda x: x[0])
        employees_df['PTO_Code'] = pto_status.apply(lambda x: x[1])

        return employees_df

    # ========================================================================
    # UTILITIES
    # ========================================================================

    def _parse_shift_time(self, time_str) -> Optional[time]:
        """Parse time string to time object"""
        try:
            time_str = str(time_str).strip()
            if isinstance(time_str, time):
                return time_str

            time_upper = time_str.upper()
            if time_upper in ['X', '', 'NAN', 'NONE']:
                return None

            if isinstance(time_str, datetime):
                return time_str.time()

            try:
                return pd.to_datetime(time_str).time()
            except:
                pass

            # Parse AM/PM
            is_pm = 'PM' in time_upper
            is_am = 'AM' in time_upper
            time_clean = time_str.replace('AM', '').replace('PM', '').replace('am', '').replace('pm', '').strip()

            if ':' in time_clean:
                parts = time_clean.split(':')
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
                if is_pm and hour < 12:
                    hour += 12
                elif is_am and hour == 12:
                    hour = 0
                return time(hour, minute)

            hour = int(float(time_clean))
            if is_pm and hour < 12:
                hour += 12
            elif is_am and hour == 12:
                hour = 0
            return time(hour, 0)
        except:
            return None

    def _shift_time_to_key(self, shift_time: time) -> str:
        """Convert time object to shift key (e.g., '5:15')"""
        return f"{shift_time.hour}:{shift_time.minute:02d}"
