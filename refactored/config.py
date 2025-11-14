"""
Configuration and Constants - Single Source of Truth
All file paths, mappings, and constants in one place
"""

from pathlib import Path

# ============================================================================
# FILE PATHS
# ============================================================================

BASE_PATH = Path(r"P:\Capacity Management\Management\Automated Scheduling")

FILES = {
    'inputs': BASE_PATH / "Inputs.xlsx",
    'historical_staffing': BASE_PATH / "Historical Staffing Data.xlsx",
    'warehouse_tasks': BASE_PATH / "Warehouse Tasks.xlsx",
    'packing_templates': BASE_PATH / "Packing Templates.xlsx",
    'packing_historical': BASE_PATH / "Packing Historical Staffing Data.xlsx",
    'model': BASE_PATH / "Model.xlsb",
}

# ============================================================================
# PTO CODES
# ============================================================================

FULL_DAY_PTO_CODES = {'P', '8P', 'V', 'S', 'H', 'U', 'PTO', 'D', 'O', 'R'}

# ============================================================================
# BIN FILLING
# ============================================================================

WORKGROUP_ORDER = [
    "1-200", "2-200", "3-200", "1-400", "2-400", "3-400",
    "1-600", "2-600", "3-600", "1-800", "2-800", "3-800",
    "1-000", "Cuts",
]

WORKGROUP_PRINTERS = {
    "1-200": ["A228", "A286", "A260", "A298", "A244", "A272", "A310", "A208"],
    "2-200": ["B228", "B286", "B260", "B220", "B298", "B244", "B272", "B208", "B310", "B236"],
    "3-200": ["C220", "C286", "C244", "C260", "C310", "C228", "C272", "C208"],
    "1-400": ["A444", "A486", "A460", "A504", "A428", "A478", "A450", "A498", "A420", "A466", "A510", "A408"],
    "2-400": ["B420", "B498", "B466", "B428", "B510", "B450", "B486", "B444", "B478", "B408"],
    "3-400": ["C428", "C486", "C466", "C420", "C498", "C450", "C478", "C444", "C510", "C408"],
    "1-600": ["A618", "A682", "A660", "A702", "A626", "A650", "A672", "A712", "A644", "A606"],
    "2-600": ["B618", "B672", "B650", "B626", "B692", "B644", "B660", "B636", "B606", "B712"],
    "3-600": ["C626", "C692", "C660", "C702", "C672", "C618", "C644", "C712", "C606", "C682"],
    "1-800": ["A818", "A892", "A860", "A902", "A806", "A836", "A872"],
    "2-800": ["B818", "B892", "B850", "B912", "B860", "B826", "B882", "B836", "B902", "B872", "B806"],
    "3-800": ["C860", "C912", "C882", "C892", "C844"],
    "1-000": ["A082", "A026", "A046", "A102", "A006", "A060", "A036", "A110", "A072", "A016", "A092"],
    "Cuts": ["C818", "C836", "C806"],
}

SHIFT_PRINTERS = {
    "5:15": ["A244", "B244", "C244"],
    "6:45": ["A444", "B420", "C428", "A618", "B618", "C626", "A818", "B818", "C860", "A082"],
    "8:45": ["A286", "A486", "A682", "A892", "A026", "B286", "B498", "B672", "B892", "C286", "C486", "C692", "C912"],
    "9:40": ["A260", "A460", "A660", "A860", "A046", "B260", "B466", "B650", "B850", "C220", "C466", "C660", "C882"],
}

SHIFT_MINIMUMS = {
    "5:15": 3,
    "5:30": 4,
    "6:45": 10,
    "8:45": 13,
    "9:40": 13,
    "10:30": None
}

# ============================================================================
# RACK FILLING
# ============================================================================

TASK_TO_ROLE = {
    'C50': 'Cuts', 'C50R': 'Cuts', 'C51': 'Cuts', 'C51R': 'Cuts',
    'C52': 'Cuts', 'C52R': 'Cuts', 'C53': 'Cuts', 'C53R': 'Cuts',
    'F88': 'Parcel Freight', 'F88R': 'Parcel Freight',
    'H1': 'Hinges', 'H1R': 'Hinges', 'H2': 'Hinges', 'H2R': 'Hinges',
    'H3': 'Hinges', 'H3R': 'Hinges', 'H4': 'Hinges', 'H4R': 'Hinges',
    'H5': 'Hinges', 'H5R': 'Hinges', 'H6': 'Hinges', 'H6R': 'Hinges',
    'H7': 'Hinges', 'H7R': 'Hinges', 'H8': 'Hinges', 'H8R': 'Hinges',
    'N01': 'North Racks', 'N01R': 'North Racks', 'N02': 'North Racks', 'N02R': 'North Racks',
    'N03': 'North Racks', 'N03R': 'North Racks', 'N04': 'North Racks', 'N04R': 'North Racks',
    'N05': 'North Racks', 'N05R': 'North Racks', 'N06': 'North Racks', 'N06R': 'North Racks',
    'N07': 'North Racks', 'N07R': 'North Racks', 'N08': 'North Racks', 'N08R': 'North Racks',
    'S89': 'South Racks', 'S89R': 'South Racks', 'S90': 'South Racks', 'S90R': 'South Racks',
    'S91': 'South Racks', 'S91R': 'South Racks', 'S92': 'South Racks', 'S92R': 'South Racks',
    'S93': 'South Racks', 'S93R': 'South Racks', 'S94': 'South Racks', 'S94R': 'South Racks',
    'North': 'Tugger', 'Float': 'Tugger', 'All': 'Tugger', 'Hinges': 'Tugger',
    'FR': 'Floor Responder',
    'Tubes': 'Tubes',
}

ROLE_TO_TASKS = {
    'North Racks': ['N01', 'N02', 'N03', 'N04', 'N05', 'N06', 'N07', 'N08'],
    'South Racks': ['S89', 'S90', 'S91', 'S92', 'S93', 'S94'],
    'Hinges': ['H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8'],
    'Cuts': ['C50', 'C51', 'C52', 'C53'],
    'Parcel Freight': ['F88'],
    'Tugger': ['Tugger'],
    'Floor Responder': ['FR'],
    'Tubes': ['Tubes'],
}

# ============================================================================
# FREIGHT
# ============================================================================

MAIN_FREIGHT_SHIFTS = {
    '8:00': 1,
    '9:30': 3,
    '10:00': 1,
}

AUX_FREIGHT_SHIFTS = {
    '8:20': 1,
    '9:20': 14,
}

MAIN_FREIGHT_ROLE_TO_CT = {
    'Packer / Tugger': 'Freight Main - Packing',
    'Scaler': 'Freight Main - Scaling/TAB Loader',
    'Packer': 'Freight Main - Packing',
    'Binning': 'Freight Main - Binning/Exceptions',
    'Shuttler': 'Freight Main - Shuttler',
}

AUX_FREIGHT_ROLE_TO_CT = {
    'Turret': 'Freight  AUX - Turret Filling',
    'Tray 1': 'Freight AUX - Filling',
    'Tray 3': 'Freight AUX - Filling',
    'Forklift': 'Freight AUX - Forklift Filling "FORK"',
    'Packer 1': 'Freight AUX - Packing',
    'Packer 2': 'Freight AUX - Packing',
    'Shuttler': 'Freight AUX - Shuttler',
    'Scaler 1': 'Freight AUX - Scaler',
    'Scaler 2': 'Freight AUX - Scaler',
    'Binning/Exceptions': 'Freight AUX - Binning/Exceptions',
    'Shuttler/Scaler1': ['Freight AUX - Shuttler', 'Freight AUX - Scaler'],
    'Extra': None,
}

# ============================================================================
# CROSS TRAINING COLUMN INDICES
# ============================================================================

CT_COLUMNS = {
    'bf_supplies': 21,
    'bf_replen': 19,
    'bf_cuts': 17,
    'bf_fr': 102,
    'rf_op': 22,
    'rf_cuts': 23,
    'rf_hinges': 24,
    'rf_tugger': 25,
    'rf_parcel': 26,
    'rf_replen': 27,
    'rf_tubes': 28,
    'rf_fr': 102,
    'lp_dr': 50,
    'lp_support': 104,
    'ps_recycle': 52,
    'ps_forklift': 55,
    'ps_additional_handling': 56,
    'ps_trash_tugging': 57,
    'ps_barge_bld': 61,
    'wc_counter': 67,
    'wc_notes': 68,
}
