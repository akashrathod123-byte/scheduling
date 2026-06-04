#!/usr/bin/env python3
"""
Supply Side Scheduling — Step 1
Generates weekly assignments for all departments and writes to Week Ahead.xlsx.
After reviewing/editing Week Ahead, run Supply Side Schedule Writer.py to push to the schedule.
"""

try:
    from tool_base import Tool
except (ImportError, ModuleNotFoundError):
    class Tool:
        pass

import os
import random
import pandas as pd
from openpyxl import load_workbook
import numpy as np
from scipy.optimize import linear_sum_assignment
from datetime import datetime, timedelta

CONFIG_PATH        = r"P:\Sales Side Operations\Coordinated Models\Automated Scheduling\Supply Side\Inputs.xlsx"
CONFIG_SHEET_FILES = "Files"
BCK_SHEET          = "BCK"
DAY_NAMES          = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def _fmt_date(val) -> str:
    if isinstance(val, datetime):
        return f"{val.month}/{val.day}/{str(val.year)[2:]}"
    try:
        d = pd.to_datetime(str(val).strip())
        return f"{d.month}/{d.day}/{str(d.year)[2:]}"
    except:
        return str(val).strip()


def load_config() -> dict:
    wb       = load_workbook(CONFIG_PATH, read_only=True, data_only=True)
    ws_files = wb[CONFIG_SHEET_FILES]

    monday_str = _fmt_date(ws_files["C7"].value)
    monday     = datetime.strptime(monday_str, "%m/%d/%y")

    week_dates = {
        day: _fmt_date(monday + timedelta(days=i))
        for i, day in enumerate(DAY_NAMES)
    }

    # Read all file paths from the Files tab
    paths = {}
    for row in ws_files.iter_rows(min_row=1, values_only=True):
        label = str(row[1]).strip() if row[1] else ''
        val   = str(row[2]).strip() if row[2] else ''
        if label and val and val != 'None':
            paths[label] = val

    config = {
        "historical_file": paths.get('Historical Staffing Data', ''),
        "ct_file":         paths.get('Cross Training Log', ''),
        "schedule_date":   monday_str,
        "week_dates":      week_dates,
        "week_ahead":      paths.get('Week Ahead', ''),
        "schedule_file":   paths.get('Schedule', ''),
        "ot_file":         paths.get('OT Sheet', ''),
    }

    ws_bck            = wb[BCK_SHEET]
    all_stations      = []
    eligible_stations = []   # Tier 1: Type == 'PO' — primary rotation pool
    overflow_stations = []   # Tier 2: Type == 'PO/TRN' — usable if not pre-filled
    last_resort_stations = []  # Tier 3: Type == 'PO/Returns' — last resort before Extra
    fixed             = {}
    pairs             = []

    for row in ws_bck.iter_rows(min_row=2, values_only=True):
        a = row[0]
        b = row[1] if len(row) > 1 else None
        t = row[2] if len(row) > 2 else None
        if a is None:
            continue
        try:
            station = int(a)
        except:
            continue
        all_stations.append(station)
        sta_type = str(t).strip() if t else ''
        if sta_type == 'PO':
            eligible_stations.append(station)
        elif sta_type == 'PO/TRN':
            overflow_stations.append(station)
        elif sta_type == 'PO/Returns':
            last_resort_stations.append(station)
        # Pure 'Returns' stations are excluded entirely
        if b and str(b).strip():
            fixed[station] = str(b).strip()

    for row in ws_bck.iter_rows(min_row=3, values_only=True):
        f = row[5] if len(row) > 5 else None
        g = row[6] if len(row) > 6 else None
        if f and g and str(f).strip() and str(g).strip():
            pairs.append((str(f).strip(), str(g).strip()))

    # BSK tab — optional. Holds names of employees currently in BSK training.
    bsk_training = set()
    if "BSK" in wb.sheetnames:
        ws_bsk = wb["BSK"]
        for row in ws_bsk.iter_rows(min_row=2, values_only=True):
            val = row[0] if row else None
            if val and str(val).strip():
                bsk_training.add(str(val).strip())

    # RSK tab — optional. Holds fixed-role assignments (Cuts, Sizer, Closing Stock, HL).
    rsk_fixed = {}
    if "RSK" in wb.sheetnames:
        ws_rsk = wb["RSK"]
        for row in ws_rsk.iter_rows(min_row=1, values_only=True):
            if row[0] and row[1]:
                rsk_fixed[str(row[0]).strip()] = str(row[1]).strip()

    # Confirmations tab: "Do Not Ask" lists, keyed by role label (matching Week Ahead row label).
    # Layout per column: row 1 = role label, rows 2+ = employee names who decline that role.
    do_not_ask = {}
    if "Confirmations" in wb.sheetnames:
        ws_conf = wb["Confirmations"]
        for c in range(1, ws_conf.max_column + 1):
            role_label = ws_conf.cell(row=1, column=c).value
            if not role_label:
                continue
            role_label = str(role_label).strip()
            decliners  = set()
            for r in range(2, ws_conf.max_row + 1):
                n = ws_conf.cell(row=r, column=c).value
                if n and str(n).strip():
                    name = str(n).strip()
                    decliners.add(name)
                    decliners.add(name.lower())
            if decliners:
                do_not_ask[role_label] = decliners

    wb.close()
    config["all_stations"]          = sorted(set(all_stations))
    config["eligible_stations"]     = sorted(set(eligible_stations))
    config["overflow_stations"]     = sorted(set(overflow_stations))
    config["last_resort_stations"]  = sorted(set(last_resort_stations))
    config["fixed"]                  = fixed
    config["pairs"]                  = pairs
    config["bsk_training"]           = bsk_training
    config["rsk_fixed"]              = rsk_fixed
    config["do_not_ask"]             = do_not_ask

    # Build CT lookup: col E (Last, First) <-> col DT (First Last)
    global _CT_LOOKUP
    ct_df = pd.read_excel(config["ct_file"], sheet_name='Cross Training', header=None)
    _CT_LOOKUP = {}
    for i in range(5, len(ct_df)):
        col_e  = str(ct_df.iloc[i, 4]).strip()   if pd.notna(ct_df.iloc[i, 4])   else ''
        col_dt = str(ct_df.iloc[i, 123]).strip()  if pd.notna(ct_df.iloc[i, 123]) else ''
        if col_e and col_e != 'nan' and col_dt and col_dt != 'nan':
            _CT_LOOKUP[col_e]          = col_dt
            _CT_LOOKUP[col_e.lower()]  = col_dt
            _CT_LOOKUP[col_dt]         = col_dt
            _CT_LOOKUP[col_dt.lower()] = col_dt

    print(f"✓ Config loaded — week of {monday_str}")
    print(f"  " + "  ".join(f"{d} {week_dates[d]}" for d in DAY_NAMES))
    print(f"  {len(all_stations)} stations | "
          f"{len(eligible_stations)} PO (rotation) | "
          f"{len(overflow_stations)} PO/TRN (overflow) | "
          f"{len(last_resort_stations)} PO/Returns (last resort) | "
          f"{len(fixed)} fixed | {len(pairs)} pairs")
    if do_not_ask:
        print(f"  Do-Not-Ask: " + "; ".join(f"{role}={len([n for n in names if not n.islower()])}" for role, names in do_not_ask.items()))
    return config


# ── Pre-filled Week Ahead ─────────────────────────────────────────────────────

def load_week_ahead_prefills(config: dict) -> dict:
    """
    Read Week Ahead.xlsx before scheduling.
    Returns {dept: {day: {'slots': {role: name}, 'placed': set(names)}}}
    so that scheduling logic can:
      - skip already-filled named slots
      - exclude already-placed employees from rotation pools
    """
    dest = config.get("week_ahead", "")
    if not dest:
        return {}

    try:
        wb = load_workbook(dest, read_only=True, data_only=True)
        ws = wb['Week Ahead']
    except Exception:
        return {}

    DEPT_COL_START = {'BCK': 1, 'MC': 8, 'BSK': 15, 'IAG': 22, 'RCK': 29, 'RSK': 36, 'AUX': 43}
    DAY_OFFSETS    = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5}
    # Names in these rows count as occupied (removed from rotation pools)
    # but don't protect a named operational slot
    PLACED_ONLY_LABELS = {'Extra', 'TRN', 'PTO', 'Other'}
    SKIP_VALUES        = {'None', 'nan', 'PTO', 'TRN', 'Extra', 'Other', ''}

    max_row = ws.max_row
    result  = {}

    for dept, col_start in DEPT_COL_START.items():
        dept_data = {day: {'slots': {}, 'placed': set()} for day in DAY_NAMES}
        for r in range(2, max_row + 1):
            label_cell = ws.cell(row=r, column=col_start)
            label = str(label_cell.value).strip() if label_cell.value else ''
            if not label:
                continue
            placed_only = label in PLACED_ONLY_LABELS
            for day, day_off in DAY_OFFSETS.items():
                name_cell = ws.cell(row=r, column=col_start + day_off)
                name = str(name_cell.value).strip() if name_cell.value else ''
                if name and name not in SKIP_VALUES:
                    dept_data[day]['placed'].add(name)
                    dept_data[day]['placed'].add(name.lower())
                    if not placed_only:
                        dept_data[day]['slots'][label] = name
        result[dept] = dept_data

    # ── Cross-department rule (universal) ─────────────────────────────────────
    # This is a dynamic, interactive scheduling tool: a person pre-filled into
    # ANY department on a given day is "spoken for" that day and must not be
    # auto-assigned in any OTHER department — not even their home department.
    # (e.g. a BSK employee pre-filled into BCK Mon–Wed must not also rotate into
    # BSK Mon–Wed, but is still free to rotate Thu–Fri.)
    #
    # We fold a global per-day "placed" union into every department's per-day
    # placed set, so each department's existing exclusion logic enforces it
    # automatically. Only 'placed' is shared — 'slots' stay per-department, so
    # operational slot protection and station-prefill detection are untouched.
    for day in DAY_NAMES:
        global_placed_today = set()
        for dept in result:
            global_placed_today |= result[dept][day]['placed']
        for dept in result:
            result[dept][day]['placed'] |= global_placed_today

    wb.close()
    return result


# ── PTO ───────────────────────────────────────────────────────────────────────

FULL_DAY_PTO_CODES = {'P', '8P', 'V', 'T', 'S', 'H', 'U', 'PTO', 'D', 'O', 'R', 'AH', 'PSL'}
LEAVE_CODES        = {'R'}


def load_pto_sheet() -> pd.DataFrame:
    return pd.read_excel(CONFIG_PATH, sheet_name="PTO", header=None)


def load_pto_exclusions(schedule_date: str, pto_df: pd.DataFrame) -> set:
    date_cols = {}
    for i in range(2, len(pto_df.columns)):
        val = pto_df.iloc[0, i]
        if pd.notna(val):
            try:
                d = pd.to_datetime(val)
                date_cols[f"{d.month}/{d.day}/{str(d.year)[2:]}"] = i
            except:
                continue
    if schedule_date not in date_cols:
        print(f"  ⚠ {schedule_date} not found in PTO tab")
        return set()
    col_idx  = date_cols[schedule_date]
    excluded = set()
    for i in range(1, len(pto_df)):
        name = pto_df.iloc[i, 1]
        if pd.isna(name):
            continue
        name = str(name).strip()
        code = str(pto_df.iloc[i, col_idx]).strip() if pd.notna(pto_df.iloc[i, col_idx]) else ''
        if code in FULL_DAY_PTO_CODES:
            excluded.add(name)
            excluded.add(name.lower())
    return excluded


def load_leave_exclusions(schedule_date: str, pto_df: pd.DataFrame) -> set:
    """Return employees on leave codes (excluded from scheduling AND from PTO section in Week Ahead)."""
    date_cols = {}
    for i in range(2, len(pto_df.columns)):
        val = pto_df.iloc[0, i]
        if pd.notna(val):
            try:
                d = pd.to_datetime(val)
                date_cols[f"{d.month}/{d.day}/{str(d.year)[2:]}"] = i
            except:
                continue
    if schedule_date not in date_cols:
        return set()
    col_idx = date_cols[schedule_date]
    on_leave = set()
    for i in range(1, len(pto_df)):
        name = pto_df.iloc[i, 1]
        if pd.isna(name):
            continue
        name = str(name).strip()
        code = str(pto_df.iloc[i, col_idx]).strip() if pd.notna(pto_df.iloc[i, col_idx]) else ''
        if code in LEAVE_CODES:
            on_leave.add(name)
            on_leave.add(name.lower())
    return on_leave


# Built at startup from CT log — maps any name form to the col DT display name
_CT_LOOKUP: dict = {}   # {col_e: col_dt, col_dt: col_dt, lowered variants too}


def ct_display(name: str) -> str:
    """Return the CT log col DT (First Last) display name for any name format."""
    return _CT_LOOKUP.get(name) or _CT_LOOKUP.get(name.lower()) or name


def in_pto(name: str, pto_set: set) -> bool:
    """Check if a name is in a PTO set, handling both name formats via CT log."""
    return name in pto_set or ct_display(name) in pto_set


def _expand_name_formats(names: set) -> set:
    """Expand a set of names to include both col E and col DT forms from the CT log."""
    expanded = set()
    for name in names:
        expanded.add(name)
        display = ct_display(name)
        expanded.add(display)
        expanded.add(display.lower())
    return expanded


def load_week_pto(week_dates: dict) -> tuple:
    pto_df       = load_pto_sheet()
    pto_by_day   = {}
    leave_by_day = {}
    for day_name, date_str in week_dates.items():
        raw_pto   = load_pto_exclusions(date_str, pto_df)
        raw_leave = load_leave_exclusions(date_str, pto_df)
        # Count only original-case names (not lowercase duplicates)
        pto_count   = sum(1 for n in raw_pto if not n.islower()) - sum(1 for n in raw_leave if not n.islower())
        leave_count = sum(1 for n in raw_leave if not n.islower())
        pto_by_day[day_name]   = _expand_name_formats(raw_pto)
        leave_by_day[day_name] = _expand_name_formats(raw_leave)
        print(f"  PTO {day_name} ({date_str}): {pto_count} out | leave: {leave_count}")
    return pto_by_day, leave_by_day


# ── Employee / History loading ────────────────────────────────────────────────

def load_supply_side_employees(ct_file: str) -> set:
    df       = pd.read_excel(ct_file, sheet_name='Cross Training', header=None)
    NAME_COL = 123
    names    = set()
    for i in range(5, len(df)):
        area = str(df.iloc[i, 0]).strip() if pd.notna(df.iloc[i, 0]) else ''
        name = str(df.iloc[i, NAME_COL]).strip() if pd.notna(df.iloc[i, NAME_COL]) else ''
        if area == 'Supply Side' and name and name != 'nan':
            names.add(name)
    return names


def load_supply_side_employees_by_dept(ct_file: str, dept: str) -> set:
    """Return First Last names of Supply Side employees currently in a given dept."""
    df    = pd.read_excel(ct_file, sheet_name='Cross Training', header=None)
    names = set()
    for i in range(5, len(df)):
        area   = str(df.iloc[i, 0]).strip()   if pd.notna(df.iloc[i, 0])   else ''
        d      = str(df.iloc[i, 1]).strip()   if pd.notna(df.iloc[i, 1])   else ''
        col_dt = str(df.iloc[i, 123]).strip() if pd.notna(df.iloc[i, 123]) else ''
        if area == 'Supply Side' and d == dept and col_dt and col_dt != 'nan':
            names.add(col_dt)
    return names


def load_historical_tasks(historical_file: str, supply_side_names: set) -> pd.DataFrame:
    hist      = pd.read_excel(historical_file, sheet_name='Historical Data', header=0)
    name_col  = hist.columns[0]
    dept_col  = hist.columns[1]
    date_cols = hist.columns[2:]

    valid_cols = {}
    for col in date_cols:
        try:
            valid_cols[col] = pd.to_datetime(col).date()
        except:
            continue

    records = []
    for _, row in hist.iterrows():
        emp = str(row[name_col]).strip()
        if not emp or emp == 'nan' or emp not in supply_side_names:
            continue
        dept = str(row[dept_col]).strip() if pd.notna(row[dept_col]) else ''
        for col, dt in valid_cols.items():
            val = row[col]
            if pd.isna(val) or str(val).strip() == '':
                continue
            records.append({'Employee': emp, 'Department': dept, 'Date': dt, 'Raw': str(val).strip()})

    result = pd.DataFrame(records) if records else pd.DataFrame(columns=['Employee', 'Department', 'Date', 'Raw'])
    result = result.sort_values(['Employee', 'Date']).reset_index(drop=True)
    print(f"✓ Loaded {len(result)} historical records for {result['Employee'].nunique()} employees")
    return result


def get_last_station(emp_name: str, hist_df: pd.DataFrame) -> int | None:
    emp_hist = hist_df[hist_df['Employee'] == emp_name].sort_values('Date', ascending=False)
    for _, row in emp_hist.iterrows():
        for part in row['Raw'].split(','):
            part = part.strip()
            if part.startswith('Bin Checker-'):
                try:
                    return int(part.split('Bin Checker-')[1].split(':')[0])
                except:
                    continue
    return None


def get_last_bsk_zone(emp_name: str, hist_df: pd.DataFrame) -> str | None:
    emp_hist = hist_df[hist_df['Employee'] == emp_name].sort_values('Date', ascending=False)
    for _, row in emp_hist.iterrows():
        for part in row['Raw'].split(','):
            part = part.strip()
            if part.startswith('Bin Stock-'):
                try:
                    zone = part.split('Bin Stock-')[1].split(':')[0].strip()
                    if zone in BSK_ROTATION:
                        return zone
                except:
                    continue
    return None


# ── Rotation helpers ──────────────────────────────────────────────────────────

def rotation_distance(last: int, candidate: int, station_list: list) -> int:
    n = len(station_list)
    if last not in station_list:
        return n
    li = station_list.index(last)
    ci = station_list.index(candidate) if candidate in station_list else -1
    if ci == -1:
        return n
    return (ci - li) % n


def best_adjacent_pair(last1: int, last2: int, available: list, station_list: list) -> tuple | None:
    best, best_dist = None, float('inf')
    avail_set = set(available)
    for s1 in available:
        s2 = s1 + 1
        if s2 in avail_set:
            d1 = rotation_distance(last1 or 0, s1, station_list)
            d2 = rotation_distance(last2 or 0, s2, station_list)
            if d1 == 0: d1 = 500
            if d2 == 0: d2 = 500
            d = d1 + d2
            if d < best_dist:
                best_dist, best = d, (s1, s2)
    return best


def best_adjacent_run(last_stations: list, available: list, station_list: list) -> list | None:
    """Find N consecutive station numbers for an N-person chain.
    Returns a list of N station numbers or None if no contiguous run exists.
    Minimizes total rotation distance from each person's last station.
    """
    n = len(last_stations)
    if n == 0:
        return None
    if n == 1:
        # Pick the best single station
        best, best_d = None, float('inf')
        for s in available:
            d = rotation_distance(last_stations[0] or 0, s, station_list)
            if d == 0: d = 500
            if d < best_d:
                best_d, best = d, s
        return [best] if best is not None else None
    avail_set = set(available)
    best, best_dist = None, float('inf')
    for s in available:
        run = list(range(s, s + n))
        if not all(x in avail_set for x in run):
            continue
        d = 0
        for i, sta in enumerate(run):
            di = rotation_distance(last_stations[i] or 0, sta, station_list)
            if di == 0: di = 500
            d += di
        if d < best_dist:
            best_dist, best = d, run
    return best


def build_pair_groups(pairs: list) -> list:
    """Convert pair-list into connected groups, ordered as a chain so any
    person who appears in multiple pairs sits between their partners.
    Returns a list of lists, each inner list is an ordered chain of names."""
    from collections import defaultdict
    partners = defaultdict(set)
    for a, b in pairs:
        partners[a].add(b)
        partners[b].add(a)

    visited = set()
    groups  = []
    for person in partners:
        if person in visited:
            continue
        # BFS to find connected component
        component = set()
        queue = [person]
        while queue:
            p = queue.pop(0)
            if p in component:
                continue
            component.add(p)
            for nb in partners[p]:
                if nb not in component:
                    queue.append(nb)
        visited.update(component)
        # Order the component as a chain: start at a degree-1 endpoint
        comp_set = component
        degrees = {p: len(partners[p] & comp_set) for p in component}
        endpoints = [p for p, d in degrees.items() if d == 1]
        if not endpoints:
            # Cycle — just take any order
            chain = list(component)
        else:
            start = sorted(endpoints)[0]  # deterministic
            chain = [start]
            used  = {start}
            while True:
                last = chain[-1]
                nexts = sorted(p for p in partners[last] if p in comp_set and p not in used)
                if not nexts:
                    break
                chain.append(nexts[0])
                used.add(nexts[0])
        groups.append(chain)
    return groups


# ── BCK Assignment ────────────────────────────────────────────────────────────

def assign_bin_checking(hist_df: pd.DataFrame, config: dict, pto_by_day: dict, prefills: dict = None) -> pd.DataFrame:
    all_stations         = config["all_stations"]
    eligible_stations    = config.get("eligible_stations", all_stations)     # Tier 1: PO
    overflow_stations    = config.get("overflow_stations", [])                # Tier 2: PO/TRN
    last_resort_stations = config.get("last_resort_stations", [])             # Tier 3: PO/Returns
    fixed                = config["fixed"]
    pairs                = config["pairs"]
    results              = []
    assigned             = set(fixed.keys())

    # Per-day "placed" set for BCK (already folded with the global cross-department
    # union in load_week_ahead_prefills). Anyone spoken for on a given day — whether
    # pre-filled in BCK or in another department — is left blank for that day so a
    # fixed/pair person is never double-booked.
    bck_placed_by_day = {day: (prefills or {}).get('BCK', {}).get(day, {}).get('placed', set())
                         for day in DAY_NAMES}

    def day_vals_for(name, station):
        out = {}
        for day in DAY_NAMES:
            if in_pto(name, pto_by_day[day]):
                out[day] = 'PTO'
            elif in_pto(name, bck_placed_by_day[day]):
                out[day] = ''   # spoken for elsewhere (or pre-filled here) — leave blank
            else:
                out[day] = station
        return out

    def is_pto_all_week(name):
        return all(in_pto(name, pto_by_day[day]) for day in DAY_NAMES)

    # Fixed
    for station, name in fixed.items():
        last = get_last_station(name, hist_df)
        dist = (station - last) if last is not None else None
        note = 'Fixed — Full Week PTO' if is_pto_all_week(name) else 'Fixed'
        results.append({'Employee': name, **day_vals_for(name, station),
                        'Last_Station': last, 'Distance': dist, 'Note': note})

    # Collect pre-placed employees across the whole week
    bck_all_placed = set()
    for day in DAY_NAMES:
        bck_all_placed.update((prefills or {}).get('BCK', {}).get(day, {}).get('placed', set()))

    # Collect pre-filled stations across the whole week (union — treat as unavailable for weekly assignment)
    prefilled_stations_week = set()
    prefilled_by_day = {}  # {day: set(stations)}
    for day in DAY_NAMES:
        day_slots = (prefills or {}).get('BCK', {}).get(day, {}).get('slots', {})
        day_prefilled = set()
        for label in day_slots:
            try:
                day_prefilled.add(int(label.replace('Station', '').strip().split()[0]))
            except:
                pass
        prefilled_by_day[day]       = day_prefilled
        prefilled_stations_week    |= day_prefilled

    # Pairs — restricted to eligible (PO-type) stations only, and never on a
    # station that's already pre-filled in Week Ahead. Pre-filled cells are
    # protected at write time, so a pair landing on one would be silently
    # dropped — the member vanishes and the whole rotation shifts by a seat.
    pair_names = {name for pair in pairs for name in pair}
    available  = [s for s in eligible_stations
                  if s not in assigned and s not in prefilled_stations_week]

    # Build connected groups from pairs so anyone appearing in multiple pairs
    # gets ONE station between their partners (e.g. Sephi-Vanessa-Jennifer at 4-5-6
    # instead of Vanessa getting two stations).
    pair_groups = build_pair_groups(pairs)

    for chain in pair_groups:
        last_stations = [get_last_station(n, hist_df) for n in chain]
        run = best_adjacent_run(last_stations, available, eligible_stations)
        if run:
            for i, name in enumerate(chain):
                station = run[i]
                last    = last_stations[i]
                dist    = rotation_distance(last or 0, station, eligible_stations) if last else None
                if len(chain) == 2:
                    partner_label = f'Pair with {chain[1 - i]}'
                else:
                    others = [chain[j] for j in range(len(chain)) if j != i]
                    partner_label = f'Pair with {" & ".join(others)}'
                note = f'{partner_label} — Full Week PTO' if is_pto_all_week(name) else partner_label
                results.append({'Employee': name, **day_vals_for(name, station),
                                'Last_Station': last, 'Distance': dist, 'Note': note})
            assigned.update(run)
            available = [s for s in available if s not in assigned]
        else:
            # No contiguous run of N stations is free (department full). Write the
            # pair members as Extra so they still show up on the schedule instead
            # of leaving blank cells that get skipped — a missing person throws the
            # whole rotation off.
            for name in chain:
                results.append({'Employee': name,
                                **{day: 'PTO' if in_pto(name, pto_by_day[day]) else 'Extra'
                                   for day in DAY_NAMES},
                                'Last_Station': get_last_station(name, hist_df),
                                'Distance': None,
                                'Note': f'Extra — no run of {len(chain)} adjacent stations'})

    # Remaining pool — everyone not fixed/paired, currently in BCK dept
    current_bck   = load_supply_side_employees_by_dept(config["ct_file"], 'Bin Receiving')
    bin_receiving = hist_df[hist_df['Department'] == 'Bin Receiving']['Employee'].unique()

    all_remaining = [e for e in sorted(bin_receiving)
                     if e not in pair_names and e not in fixed.values()
                     and (e in current_bck or ct_display(e) in current_bck)
                     and not in_pto(e, bck_all_placed)]

    full_pto_emps  = [e for e in all_remaining if is_pto_all_week(e)]
    remaining_emps = [e for e in all_remaining if not is_pto_all_week(e)]

    for emp in full_pto_emps:
        last = get_last_station(emp, hist_df)
        results.append({'Employee': emp, **{day: 'PTO' for day in DAY_NAMES},
                        'Last_Station': last, 'Distance': None, 'Note': 'Full Week PTO'})

    # Weekly Hungarian — tiered station pool:
    #   Tier 1 (PO):           normal rotation cost (1..500)
    #   Tier 2 (PO/TRN):       cost + 600 — used only after Tier 1 is full
    #   Tier 3 (PO/Returns):   cost + 800 — last resort before Extra
    #   Extra (padded fake):   999 — only if every real station is taken
    remaining_t1 = [s for s in eligible_stations    if s not in assigned and s not in prefilled_stations_week]
    remaining_t2 = [s for s in overflow_stations    if s not in assigned and s not in prefilled_stations_week]
    remaining_t3 = [s for s in last_resort_stations if s not in assigned and s not in prefilled_stations_week]
    remaining_stations = remaining_t1 + remaining_t2 + remaining_t3
    station_tier = {s: 1 for s in remaining_t1}
    station_tier.update({s: 2 for s in remaining_t2})
    station_tier.update({s: 3 for s in remaining_t3})
    TIER_PENALTY = {1: 0, 2: 600, 3: 800}

    if remaining_emps and remaining_stations:
        n_emps          = len(remaining_emps)
        padded_stations = remaining_stations + [None] * max(0, n_emps - len(remaining_stations))
        cost = np.zeros((n_emps, len(padded_stations)))
        for i, emp in enumerate(remaining_emps):
            last = get_last_station(emp, hist_df)
            for j, sta in enumerate(padded_stations):
                if sta is None:
                    cost[i, j] = 999
                else:
                    tier = station_tier.get(sta, 1)
                    if tier == 1:
                        d = rotation_distance(last or 0, sta, eligible_stations)
                        cost[i, j] = 500 if d == 0 else d
                    else:
                        # Flat tier penalty (no rotation distance — these aren't in the cycle)
                        cost[i, j] = TIER_PENALTY[tier]

        row_ind, col_ind = linear_sum_assignment(cost)
        emp_to_station   = {remaining_emps[i]: padded_stations[j] for i, j in zip(row_ind, col_ind)}

        for emp in remaining_emps:
            last    = get_last_station(emp, hist_df)
            station = emp_to_station.get(emp)
            if station is not None:
                tier = station_tier.get(station, 1)
                if tier == 1:
                    dist = rotation_distance(last or 0, station, eligible_stations) if last else None
                    note = 'Rotation +1' if dist == 1 else ('Blocked by fixed/pairs' if dist and dist > 1 else 'Optimized')
                elif tier == 2:
                    dist = None
                    note = 'PO/TRN overflow'
                else:
                    dist = None
                    note = 'PO/Returns last resort'
                # Build per-day values: use assigned station unless pre-filled that day
                day_vals = {}
                for day in DAY_NAMES:
                    if in_pto(emp, pto_by_day[day]):
                        day_vals[day] = 'PTO'
                    elif station in prefilled_by_day[day]:
                        # Their station is pre-filled this day — mark as extra
                        day_vals[day] = 'Extra'
                    else:
                        day_vals[day] = station
                results.append({'Employee': emp, **day_vals,
                                'Last_Station': last, 'Distance': dist, 'Note': note})
            else:
                results.append({'Employee': emp,
                                **{day: 'PTO' if in_pto(emp, pto_by_day[day]) else 'Extra' for day in DAY_NAMES},
                                'Last_Station': last, 'Distance': None, 'Note': 'Extra'})
    elif remaining_emps:
        # Every real station is taken (fixed/pairs/pre-fills consumed them all).
        # The Hungarian block above is skipped, so write everyone left as Extra —
        # otherwise they'd be dropped from the schedule entirely.
        for emp in remaining_emps:
            last = get_last_station(emp, hist_df)
            results.append({'Employee': emp,
                            **{day: 'PTO' if in_pto(emp, pto_by_day[day]) else 'Extra' for day in DAY_NAMES},
                            'Last_Station': last, 'Distance': None, 'Note': 'Extra — all stations full'})

    # Second pass — reassign blocked
    assigned_stations = set()
    for r in results:
        note = r.get('Note', '')
        if 'Full Week PTO' in note or 'Fixed — Full Week PTO' in note:
            continue
        for day in DAY_NAMES:
            val = r.get(day)
            if isinstance(val, (int, float)) and pd.notna(val):
                assigned_stations.add(int(val))
    open_stations = [s for s in eligible_stations if s not in assigned_stations and s not in prefilled_stations_week]

    already_improved = set()
    keep_going = True
    while keep_going:
        keep_going = False
        candidates = sorted(
            [r for r in results
             if r.get('Distance') is not None and r['Distance'] > 1
             and r['Employee'] not in already_improved
             and not any(x in r.get('Note', '') for x in ['Fixed', 'Pair with', 'Extra', 'PTO'])],
            key=lambda r: r['Distance'], reverse=True
        )
        for r in candidates:
            emp  = r['Employee']
            last = r.get('Last_Station')
            if last is None or last not in eligible_stations:
                continue
            best_station, best_dist = None, float('inf')
            for s in open_stations:
                d = rotation_distance(int(last), s, eligible_stations)
                if d == 0: d = 500
                if d < best_dist:
                    best_dist, best_station = d, s
            if best_station is None or best_dist >= r['Distance']:
                continue
            current = next((r[day] for day in DAY_NAMES if isinstance(r.get(day), (int, float))), None)
            if current is not None:
                open_stations.append(int(current))
            open_stations.remove(best_station)
            for day in DAY_NAMES:
                if r[day] != 'PTO':
                    r[day] = best_station
            r['Distance'] = best_dist
            r['Note']     = 'Rotation +1' if best_dist == 1 else 'Optimized (was blocked)'
            already_improved.add(emp)
            keep_going = True
            break

    # Unassigned stations — only show among ELIGIBLE
    assigned_stations = set()
    for r in results:
        for day in DAY_NAMES:
            val = r.get(day)
            if isinstance(val, (int, float)) and pd.notna(val):
                assigned_stations.add(int(val))
    for station in eligible_stations:
        if station not in assigned_stations and station not in prefilled_stations_week:
            results.append({'Employee': '— Open —', **{day: station for day in DAY_NAMES},
                            'Last_Station': None, 'Distance': None, 'Note': 'Unassigned'})

    df = pd.DataFrame(results, columns=[
        'Employee', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
        'Last_Station', 'Distance', 'Note'
    ])
    df['_sort'] = df[DAY_NAMES].apply(
        lambda row: next((v for v in row if isinstance(v, (int, float)) and pd.notna(v)), float('inf')), axis=1)
    df = df.sort_values('_sort', na_position='last').drop(columns='_sort').reset_index(drop=True)
    return df


# ── BSK Rotation ──────────────────────────────────────────────────────────────

BSK_ROTATION = [
    "1 Red New", "1 Red North", "1 Red South",
    "1 Blue North", "1 Blue South",
    "2 Red North", "2 Red South",
    "2 Blue North", "2 Blue South",
    "3 Red North", "3 Red South",
    "3 Blue North", "3 Blue South",
    "Floater",
]


def load_bsk_employees(ct_file: str) -> dict:
    df      = pd.read_excel(ct_file, sheet_name='Cross Training', header=None)
    headers = [str(v).strip() if pd.notna(v) else '' for v in df.iloc[4]]

    def find_col(name):
        for i, h in enumerate(headers):
            if h == name:
                return i
        return None

    name_col  = 4
    alt_col   = 123
    sizer_col = find_col('Sizer (SZB)')
    srt_col   = find_col('Sort (SRT)')
    bsk_col   = find_col('Stockkeeper (BSK)')

    all_names      = []
    qualified      = []   # has Stockkeeper (BSK) X — eligible for zone rotation
    sizer          = None
    sizer_backups  = []
    first_last_map = {}

    for i in range(5, len(df)):
        area = str(df.iloc[i, 0]).strip() if pd.notna(df.iloc[i, 0]) else ''
        dept = str(df.iloc[i, 1]).strip() if pd.notna(df.iloc[i, 1]) else ''
        name = str(df.iloc[i, name_col]).strip() if pd.notna(df.iloc[i, name_col]) else ''
        alt  = str(df.iloc[i, alt_col]).strip()  if pd.notna(df.iloc[i, alt_col])  else ''

        if area != 'Supply Side' or dept != 'Bin Stockkeeping' or not name or name == 'nan':
            continue

        all_names.append(name)
        if alt and alt != 'nan':
            first_last_map[alt.lower()] = name

        if bsk_col is not None:
            val = str(df.iloc[i, bsk_col]).strip() if pd.notna(df.iloc[i, bsk_col]) else ''
            if val.upper() == 'X':
                qualified.append(name)

        if sizer_col is not None:
            val = str(df.iloc[i, sizer_col]).strip() if pd.notna(df.iloc[i, sizer_col]) else ''
            if val.upper() == 'X' and sizer is None:
                sizer = name

        if srt_col is not None:
            val = str(df.iloc[i, srt_col]).strip() if pd.notna(df.iloc[i, srt_col]) else ''
            if val.upper() == 'X':
                sizer_backups.append(name)

    print(f"✓ BSK employees loaded: {len(all_names)} total, {len(qualified)} qualified, sizer={sizer}")
    return {'all': all_names, 'qualified': qualified, 'sizer': sizer, 'sizer_backups': sizer_backups, 'first_last_map': first_last_map}


def assign_bin_stockkeeping(config: dict, pto_by_day: dict, hist_df: pd.DataFrame, prefills: dict = None) -> pd.DataFrame:
    ct_file  = config["ct_file"]
    training = config["bsk_training"]

    print("\nLoading BSK employees...")
    bsk       = load_bsk_employees(ct_file)
    all_names = bsk['all']
    sizer     = bsk['sizer']
    backups   = bsk['sizer_backups']

    def is_pto_all_week(name):
        return all(in_pto(name, pto_by_day[day]) for day in DAY_NAMES)

    active        = [n for n in all_names if n not in training and ct_display(n) not in training]
    bsk_qual_set  = set(bsk['qualified'])
    # Only employees with Stockkeeper (BSK) X go into zone rotation; others are always Extra
    rotation_pool = [n for n in active if n in bsk_qual_set or ct_display(n) in bsk_qual_set]
    extra_always  = [n for n in active if n not in rotation_pool]

    # Deterministic per-week shuffle: same week → same order, different weeks rotate the pool.
    # This removes the persistent alphabetical bias where A-names always got optimal zones and
    # tail-of-alphabet names always ended up Extra.
    rng = random.Random(config["schedule_date"])
    shuffled_pool = list(rotation_pool)
    rng.shuffle(shuffled_pool)

    emp_days   = {emp: {} for emp in active}
    sizer_row  = {'Employee': sizer if sizer else '— No Sizer —', 'Note': 'Sizer'}

    for day in DAY_NAMES:
        pto_today = pto_by_day[day]
        # Exclude employees already placed in Week Ahead for this day
        bsk_placed = (prefills or {}).get('BSK', {}).get(day, {}).get('placed', set())
        bsk_slots  = (prefills or {}).get('BSK', {}).get(day, {}).get('slots', {})

        if sizer and in_pto(sizer, pto_today):
            day_sizer = next(
                (b for b in backups if b != sizer and not in_pto(b, pto_today) and b in active), None)
            sizer_row[day] = f'PTO → {day_sizer}' if day_sizer else 'PTO → No backup'
        else:
            sizer_row[day] = 'Sizer'

        backup_covering = None
        if isinstance(sizer_row.get(day), str) and '→' in sizer_row[day]:
            parts = sizer_row[day].split('→')
            if len(parts) > 1:
                backup_covering = parts[1].strip()

        # Step 1: exclude PTO people, the day's sizer/backup, and unqualified employees from zone rotation
        available_today = [e for e in rotation_pool if e != sizer and e != backup_covering
                           and not in_pto(e, pto_today) and not in_pto(e, bsk_placed)]
        # Mark unqualified as Extra (unless on PTO)
        for emp in extra_always:
            if in_pto(emp, pto_today):
                emp_days[emp][day] = 'PTO'
            elif in_pto(emp, bsk_placed):
                # Pre-placed somewhere by user — leave their row blank for this day so the prefill stays
                emp_days[emp].setdefault(day, '')
            elif day not in emp_days[emp]:
                emp_days[emp][day] = 'Extra'
        n_slots = len(BSK_ROTATION)

        # Step 2: compute each employee's preferred zone for today
        # Priority: yesterday's actual zone + 1 > last week's zone + day_offset > shuffled fallback
        prefilled_zones   = set(bsk_slots.keys())
        # Floater is multi-slot (3 floors). Make sure all 3 Floater positions are available unless
        # all three are already pre-filled. We treat 1st/2nd/3rd Floor Float labels as 'Floater'.
        FLOATER_LABELS = {'1st Floor Float', '2nd Floor Float', '3rd Floor Float'}
        floater_prefilled_count = sum(1 for lbl in prefilled_zones if lbl in FLOATER_LABELS)

        available_zones = [z for z in BSK_ROTATION if z not in prefilled_zones]
        # Per-week rule: fill all 3 Floater slots before pushing anyone to Extra.
        if 'Floater' in available_zones:
            extra_floaters_needed = max(0, 3 - floater_prefilled_count) - 1
            if extra_floaters_needed > 0:
                available_zones += ['Floater'] * extra_floaters_needed

        day_offset        = DAY_NAMES.index(day)
        emp_prefs         = {}
        for emp in available_today:
            # Use yesterday's actual assignment as the base if available
            prev_zone = emp_days[emp].get(DAY_NAMES[day_offset - 1]) if day_offset > 0 else None
            if prev_zone and prev_zone in BSK_ROTATION:
                base_idx = (BSK_ROTATION.index(prev_zone) + 1) % n_slots
            else:
                last_zone = get_last_bsk_zone(emp, hist_df)
                if last_zone and last_zone in BSK_ROTATION:
                    base_idx = (BSK_ROTATION.index(last_zone) + 1) % n_slots
                else:
                    base_idx = shuffled_pool.index(emp) % n_slots if emp in shuffled_pool else 0
                base_idx = (base_idx + day_offset) % n_slots
            emp_prefs[emp] = base_idx

        # Step 3: assign zones using Hungarian algorithm
        # Penalize: same zone as yesterday (heavy), rotation distance from preference (light),
        # AND push toward filling all real zones before any Extra (so Floaters fill up).
        assigned = {}
        if available_today and available_zones:
            n_e = len(available_today)
            n_z = len(available_zones)
            size = max(n_e, n_z)
            # Padded cells (i >= n_e or j >= n_z) cost zero; real assignments have positive cost.
            # To prevent Hungarian from preferring padded ("Extra") matches over real zones we make
            # real-zone cost negative-baseline so Hungarian fills real zones first.
            cost = np.full((size, size), 0.0)
            BASE = -1000  # any real-zone match is better than no assignment
            for i, emp in enumerate(available_today):
                prev_zone = emp_days[emp].get(DAY_NAMES[day_offset - 1]) if day_offset > 0 else None
                for j, zone in enumerate(available_zones):
                    rot_dist = (emp_prefs[emp] - BSK_ROTATION.index(zone)) % n_slots
                    c = BASE + rot_dist
                    if prev_zone and prev_zone == zone:
                        c += 500
                    cost[i, j] = c
            row_ind, col_ind = linear_sum_assignment(cost)
            for i, j in zip(row_ind, col_ind):
                if i < n_e and j < n_z and cost[i, j] < 0:
                    assigned[available_today[i]] = available_zones[j]

        for emp in available_today:
            emp_days[emp][day] = assigned.get(emp, 'Extra')

        # Step 4: mark PTO or Pre-placed for non-available employees
        for emp in active:
            if emp == sizer or emp == backup_covering:
                continue
            if day not in emp_days[emp]:
                if in_pto(emp, bsk_placed):
                    # Already placed by user — leave the row blank for that day
                    emp_days[emp][day] = ''
                elif in_pto(emp, pto_today):
                    emp_days[emp][day] = 'PTO'

    results = []
    # Only write sizer row if sizer is not in training
    if sizer and sizer not in training and ct_display(sizer) not in training:
        results.append({'Employee': sizer_row['Employee'],
                        **{day: sizer_row.get(day, '') for day in DAY_NAMES}, 'Note': 'Sizer'})

    for emp in sorted(active):
        if emp == sizer:
            continue
        if is_pto_all_week(emp):
            results.append({'Employee': emp, **{day: 'PTO' for day in DAY_NAMES}, 'Note': 'Full Week PTO'})
        else:
            days = emp_days.get(emp, {})
            results.append({'Employee': emp, **{day: days.get(day, 'PTO') for day in DAY_NAMES}, 'Note': ''})

    for emp in sorted(training):
        if emp == sizer:
            continue
        day_vals = {day: 'PTO' if in_pto(emp, pto_by_day[day]) else 'Training' for day in DAY_NAMES}
        results.append({'Employee': emp, **day_vals, 'Note': 'In Training'})

    return pd.DataFrame(results, columns=['Employee'] + DAY_NAMES + ['Note'])


# ── IAG Rotation ──────────────────────────────────────────────────────────────

IAG_ROTATION = [
    "Bins 1", "Racks", "Bins 2", "Floater/1st Floor",
    "Bins 3", "Float/Audits", "Counts",
]
IAG_TASK_PREFIX = "IAG-"


def load_iag_employees(ct_file: str) -> tuple:
    df       = pd.read_excel(ct_file, sheet_name='Cross Training', header=None)
    name_col = 4
    alt_col  = 123
    headers  = [str(v).strip() if pd.notna(v) else '' for v in df.iloc[4]]
    start_col = next((i for i, h in enumerate(headers) if 'Assigned Start Time' in h or 'Start Time' in h), None)

    employees     = []
    start_times   = {}
    last_to_first = {}
    racks_qualified = []  # employees with 'IAG Racks' X in CT log (col 131)

    for i in range(5, len(df)):
        area = str(df.iloc[i, 0]).strip() if pd.notna(df.iloc[i, 0]) else ''
        dept = str(df.iloc[i, 1]).strip() if pd.notna(df.iloc[i, 1]) else ''
        name = str(df.iloc[i, name_col]).strip() if pd.notna(df.iloc[i, name_col]) else ''
        if area != 'Supply Side' or dept != 'Inventory Accuracy' or not name or name == 'nan':
            continue
        employees.append(name)
        alt = str(df.iloc[i, alt_col]).strip() if pd.notna(df.iloc[i, alt_col]) else ''
        if alt and alt != 'nan':
            last_to_first[name] = alt
        if start_col is not None:
            val = df.iloc[i, start_col]
            if pd.notna(val):
                try:
                    if hasattr(val, 'hour'):
                        start_times[name] = f"{val.hour}:{val.minute:02d}"
                    else:
                        t = pd.to_datetime(str(val))
                        start_times[name] = f"{t.hour}:{t.minute:02d}"
                except:
                    start_times[name] = str(val).strip()
        racks_val = str(df.iloc[i, 131]).strip() if pd.notna(df.iloc[i, 131]) else ''
        if racks_val.upper() == 'X':
            racks_qualified.append(name)

    print(f"✓ IAG employees loaded: {len(employees)} total, {len(racks_qualified)} Racks-qualified")
    return employees, start_times, last_to_first, racks_qualified


def get_last_iag_role(emp_name: str, hist_df: pd.DataFrame, name_map: dict = None) -> str | None:
    emp_hist = hist_df[hist_df['Employee'] == ct_display(emp_name)].sort_values('Date', ascending=False)
    for _, row in emp_hist.iterrows():
        for part in row['Raw'].split(','):
            part = part.strip()
            if part.startswith(IAG_TASK_PREFIX):
                role = part[len(IAG_TASK_PREFIX):].split(':')[0].strip()
                if role in IAG_ROTATION or role == 'Desk':
                    return role
    return None


def assign_iag(config: dict, pto_by_day: dict, hist_df: pd.DataFrame, prefills: dict = None) -> pd.DataFrame:
    ct_file = config["ct_file"]
    print("\nLoading IAG employees...")
    employees, start_times, name_map, racks_qualified = load_iag_employees(ct_file)
    racks_qual_set = set(racks_qualified)

    if not employees:
        print("  ⚠ No IAG employees found")
        return pd.DataFrame(columns=['Employee'] + DAY_NAMES + ['Last_Role', 'Note'])

    def is_pto_all_week(name):
        return all(in_pto(name, pto_by_day[day]) for day in DAY_NAMES)

    desk_person = next((emp for emp in employees
                        if '6:00' in str(start_times.get(emp, '')) or '6:0' in str(start_times.get(emp, ''))), None)
    print(f"  Desk person (6am): {desk_person}")

    # IAG is weekly: assign one role per employee for the whole week,
    # excluding pre-placed employees and pre-filled slots.
    n_slots = len(IAG_ROTATION)

    # Collect all pre-placed employees and pre-filled slots across the week
    iag_all_placed = set()
    iag_all_prefilled_roles = set()
    LABEL_TO_ROLE = {
        'Desk/ Macro': 'Desk', 'Counts/Material Found': 'Counts',
        'Float/Audits ': 'Float/Audits', 'Floater/1st Floor': 'Floater/1st Floor',
    }
    for day in DAY_NAMES:
        day_data = (prefills or {}).get('IAG', {}).get(day, {})
        iag_all_placed.update(day_data.get('placed', set()))
        for lbl in day_data.get('slots', {}):
            iag_all_prefilled_roles.add(LABEL_TO_ROLE.get(lbl, lbl))

    # Rotation pool excludes desk and pre-placed employees
    rotation_employees = [e for e in employees
                          if e != desk_person and not in_pto(e, iag_all_placed)]

    # Available roles excludes anything pre-filled any day this week
    available_roles = [r for r in IAG_ROTATION if r not in iag_all_prefilled_roles]

    natural = {}
    for emp in rotation_employees:
        last_role = get_last_iag_role(emp, hist_df, name_map)
        if last_role and last_role in IAG_ROTATION:
            base_idx = (IAG_ROTATION.index(last_role) + 1) % n_slots
        else:
            sorted_emps = sorted(rotation_employees)
            base_idx = sorted_emps.index(emp) % n_slots if emp in sorted_emps else 0
        natural[emp] = base_idx

    used_slots = set()
    emp_role   = {}
    sorted_emps_by_dist = sorted(rotation_employees, key=lambda e: (
        (natural[e] - IAG_ROTATION.index(get_last_iag_role(e, hist_df, name_map))
         if get_last_iag_role(e, hist_df, name_map) and get_last_iag_role(e, hist_df, name_map) in IAG_ROTATION
         else n_slots) % n_slots
    ))
    for emp in sorted_emps_by_dist:
        idx = natural[emp]
        attempts = 0
        # Skip pre-filled roles, already-used slots, and Racks if not qualified
        while attempts < n_slots:
            role_candidate = IAG_ROTATION[idx]
            racks_blocked  = (role_candidate == 'Racks' and emp not in racks_qual_set
                              and ct_display(emp) not in racks_qual_set)
            if idx not in used_slots and role_candidate not in iag_all_prefilled_roles and not racks_blocked:
                break
            idx = (idx + 1) % n_slots
            attempts += 1
        used_slots.add(idx)
        emp_role[emp] = IAG_ROTATION[idx]

    emp_days  = {emp: {} for emp in employees}
    desk_days = {}

    for day in DAY_NAMES:
        pto_today  = pto_by_day[day]
        iag_placed = (prefills or {}).get('IAG', {}).get(day, {}).get('placed', set())

        if desk_person and in_pto(desk_person, pto_today):
            backup = next((e for e in rotation_employees
                           if emp_role.get(e) == IAG_ROTATION[0] and not in_pto(e, pto_today)), None)
            desk_days[day] = f'PTO → {backup}' if backup else 'PTO → No backup'
        else:
            desk_days[day] = 'Desk'

        for emp in rotation_employees:
            if in_pto(emp, iag_placed):
                # Leave the row empty so the user's pre-fill stays put
                emp_days[emp][day] = ''
            elif in_pto(emp, pto_today):
                my_role = emp_role.get(emp)
                if my_role:
                    my_idx = IAG_ROTATION.index(my_role)
                    backup = None
                    for offset in range(1, n_slots + 1):
                        next_role  = IAG_ROTATION[(my_idx - offset) % n_slots]
                        candidates = [e for e in rotation_employees
                                      if emp_role.get(e) == next_role and not in_pto(e, pto_today)]
                        if candidates:
                            backup = candidates[0]
                            break
                    emp_days[emp][day] = f'PTO → {backup}' if backup else 'PTO'
                else:
                    emp_days[emp][day] = 'PTO'
            else:
                emp_days[emp][day] = emp_role.get(emp, '')

    results = []
    if desk_person:
        results.append({'Employee': desk_person,
                        **{day: desk_days.get(day, 'Desk') for day in DAY_NAMES},
                        'Last_Role': 'Desk', 'Note': 'Desk (6am)'})

    def role_sort_key(emp):
        role = emp_role.get(emp, '')
        return IAG_ROTATION.index(role) if role in IAG_ROTATION else 999

    for emp in sorted(rotation_employees, key=role_sort_key):
        last_role = get_last_iag_role(emp, hist_df, name_map)
        if is_pto_all_week(emp):
            results.append({'Employee': emp, **{day: 'PTO' for day in DAY_NAMES},
                            'Last_Role': last_role or '', 'Note': 'Full Week PTO'})
        else:
            days = emp_days.get(emp, {})
            results.append({'Employee': emp, **{day: days.get(day, '') for day in DAY_NAMES},
                            'Last_Role': last_role or '', 'Note': ''})

    # Add pre-placed employees with their assigned roles from Week Ahead
    placed_emps_added = set(rotation_employees)
    if desk_person:
        placed_emps_added.add(desk_person)
    for emp in employees:
        if emp in placed_emps_added:
            continue
        if in_pto(emp, iag_all_placed):
            last_role = get_last_iag_role(emp, hist_df, name_map)
            day_vals = {}
            for day in DAY_NAMES:
                day_slots = (prefills or {}).get('IAG', {}).get(day, {}).get('slots', {})
                # Find this employee's role for this day from pre-fills
                role_this_day = next((LABEL_TO_ROLE.get(lbl, lbl)
                                      for lbl, name in day_slots.items()
                                      if name == ct_display(emp) or name == emp), None)
                if role_this_day:
                    day_vals[day] = role_this_day
                elif in_pto(emp, pto_by_day[day]):
                    day_vals[day] = 'PTO'
                else:
                    day_vals[day] = ''
            results.append({'Employee': emp, **day_vals,
                            'Last_Role': last_role or '', 'Note': 'Pre-placed'})

    return pd.DataFrame(results, columns=['Employee'] + DAY_NAMES + ['Last_Role', 'Note'])


# ── RSK Rotation ──────────────────────────────────────────────────────────────

RSK_DEPT = 'Rack Stockkeeping'

# CT log qualification columns
RSK_OP_COL      = 'Late/North/South Stockkeeper (Order Picker) (RSK)'
RSK_SHUTTLE_COL = 'Shuttle/Transport (TRS)'
RSK_TURRET_COL  = 'Turret (RSK)'
RSK_HINGE_COL   = 'Hinge Stockkeeper (Forklift) (HSK)'
RSK_WKD_COL     = 'Work Delivery (WKD)'

# Daily sub-rotation sequences
RSK_OP_SEQUENCE       = ['North 1', 'South', 'North 2']
RSK_FORKLIFT_SEQUENCE = ['Hinge 1', 'Shuttle', 'Hinge 2', 'Shuttle']
RSK_VEHICLE_ORDER     = ['OP', 'Forklift', 'Turret']

# History prefixes for last-role lookup
RSK_HISTORY_MAP = {
    'North 1':       'Rack Stock-North',
    'South':         'Rack Stock-South',
    'North 2':       'Rack Stock-North2',
    'Shuttle':       'Main Shuttler',
    'Hinge 1':       'Hinge Stock',
    'Hinge 2':       'Main Shuttler-Hinge',
    'Turret':        'Rack Stock-Turret',
    'Cuts':          'Rack Replenish-Cuts',
    'Sizer':         'Rack Sizer',
    'Closing Stock': 'Closing Stock',
    'HL':            'Hotlane',
    'WKD':           'Work Delivery',
}


def load_rsk_data(ct_file: str, rsk_fixed: dict) -> dict:
    df      = pd.read_excel(ct_file, sheet_name='Cross Training', header=None)
    headers = [str(v).strip() if pd.notna(v) else '' for v in df.iloc[4]]

    def find_col(name):
        for i, h in enumerate(headers):
            if h == name:
                return i
        return None

    name_col    = 4
    alt_col     = 123
    start_col   = find_col('Assigned Start Time')
    op_col      = find_col(RSK_OP_COL)
    shuttle_col = find_col(RSK_SHUTTLE_COL)
    turret_col  = find_col(RSK_TURRET_COL)
    hinge_col   = find_col(RSK_HINGE_COL)
    wkd_col     = find_col(RSK_WKD_COL)

    all_names        = []
    name_map         = {}
    op_qualified     = []
    shuttle_qualified = []
    turret_qualified = []
    hinge_qualified  = []
    wkd_qualified    = []
    start_times      = {}

    for i in range(5, len(df)):
        area = str(df.iloc[i, 0]).strip() if pd.notna(df.iloc[i, 0]) else ''
        dept = str(df.iloc[i, 1]).strip() if pd.notna(df.iloc[i, 1]) else ''
        name = str(df.iloc[i, name_col]).strip() if pd.notna(df.iloc[i, name_col]) else ''
        alt  = str(df.iloc[i, alt_col]).strip()  if pd.notna(df.iloc[i, alt_col])  else ''
        if area != 'Supply Side' or dept != RSK_DEPT or not name or name == 'nan':
            continue
        all_names.append(name)
        if alt and alt != 'nan':
            name_map[name] = alt
        if start_col is not None:
            val = df.iloc[i, start_col]
            if pd.notna(val):
                try:
                    if hasattr(val, 'hour'):
                        start_times[name] = f"{val.hour}:{val.minute:02d}"
                    else:
                        t = pd.to_datetime(str(val))
                        start_times[name] = f"{t.hour}:{t.minute:02d}"
                except:
                    start_times[name] = str(val).strip()
        def x(col): return col and str(df.iloc[i, col]).strip().upper() == 'X'
        if x(op_col):      op_qualified.append(name)
        if x(shuttle_col): shuttle_qualified.append(name)
        if x(turret_col):  turret_qualified.append(name)
        if x(hinge_col):   hinge_qualified.append(name)
        if x(wkd_col):     wkd_qualified.append(name)

    print(f"✓ RSK employees loaded: {len(all_names)} total")
    return {
        'all': all_names, 'name_map': name_map, 'start_times': start_times,
        'op_qualified':      op_qualified,
        'shuttle_qualified': shuttle_qualified,
        'turret_qualified':  turret_qualified,
        'hinge_qualified':   hinge_qualified,
        'wkd_qualified':     wkd_qualified,
        'cuts':          rsk_fixed.get('Cuts'),
        'sizer':         rsk_fixed.get('Sizer'),
        'closing_stock': rsk_fixed.get('Closing Stock'),
        'hl':            rsk_fixed.get('HL'),
    }


def get_last_rsk_role(emp: str, hist_df: pd.DataFrame) -> str | None:
    """Return the most recent RSK role from history."""
    first_last = ct_display(emp)
    emp_hist   = hist_df[hist_df['Employee'] == first_last].sort_values('Date', ascending=False)
    for _, row in emp_hist.iterrows():
        for part in row['Raw'].split(','):
            p = part.strip()
            for role, prefix in RSK_HISTORY_MAP.items():
                if p.startswith(prefix):
                    return role
    return None


def get_vehicle_for_role(role: str) -> str | None:
    if role in RSK_OP_SEQUENCE:       return 'OP'
    if role in ('Hinge 1', 'Hinge 2', 'Shuttle'): return 'Forklift'
    if role == 'Turret':               return 'Turret'
    return None


def assign_rsk(config: dict, pto_by_day: dict, hist_df: pd.DataFrame, prefills: dict = None) -> pd.DataFrame:
    ct_file   = config["ct_file"]
    rsk_fixed = config["rsk_fixed"]
    print("\nLoading RSK data...")
    rsk = load_rsk_data(ct_file, rsk_fixed)

    all_names = rsk['all']

    def is_pto_all_week(name):
        return all(in_pto(name, pto_by_day[day]) for day in DAY_NAMES)

    def day_vals_fixed(name, role):
        return {day: 'PTO' if in_pto(name, pto_by_day[day]) else role for day in DAY_NAMES}

    assigned_fixed = set()
    results        = []

    # ── 1. Fixed weekly roles ─────────────────────────────────────────────────
    for role_key, name in [
        ('Cuts', rsk['cuts']), ('Sizer', rsk['sizer']),
        ('Closing Stock', rsk['closing_stock']), ('HL', rsk['hl']),
    ]:
        if not name:
            results.append({'Employee': f'— {role_key} unset —',
                            **{day: role_key for day in DAY_NAMES}, 'Role': role_key, 'Note': 'Not configured'})
            continue
        assigned_fixed.add(name)
        note = 'Fixed — Full Week PTO' if is_pto_all_week(name) else 'Fixed'
        results.append({'Employee': name, **day_vals_fixed(name, role_key), 'Role': role_key, 'Note': note})

    # ── 2. WKD (7:35am + WKD qualified) ─────────────────────────────────────
    wkd_assigned = []
    for emp in rsk['wkd_qualified']:
        if emp in assigned_fixed: continue
        if '7:35' in str(rsk['start_times'].get(emp, '')):
            wkd_assigned.append(emp)
            assigned_fixed.add(emp)
            note = 'WKD — Full Week PTO' if is_pto_all_week(emp) else 'WKD'
            results.append({'Employee': emp, **day_vals_fixed(emp, 'WKD'), 'Role': 'WKD', 'Note': note})
        if len(wkd_assigned) == 2:
            break

    # ── 3. Rotating pool — everyone else ─────────────────────────────────────
    # Exclude employees pre-placed in Week Ahead for all days from pool
    rsk_all_placed = set()
    for day in DAY_NAMES:
        rsk_all_placed.update((prefills or {}).get('RSK', {}).get(day, {}).get('placed', set()))
    pool = [e for e in all_names if e not in assigned_fixed and not in_pto(e, rsk_all_placed)]

    # Each employee's vehicle sequence based purely on qualifications
    def vehicle_sequence(emp):
        seq = []
        if emp in rsk['op_qualified']:
            seq.append('OP')
        if emp in rsk['hinge_qualified'] or emp in rsk['shuttle_qualified']:
            seq.append('Forklift')
        if emp in rsk['turret_qualified']:
            seq.append('Turret')
        return seq if seq else ['OP']

    # ── Assign each person ONE vehicle for the whole week ────────────────────
    # Based on history: last vehicle → advance one step. Falls back to round-robin.
    sorted_pool = sorted(pool)
    _seq_count  = {}

    emp_vehicle = {}
    for emp in sorted_pool:
        seq       = vehicle_sequence(emp)
        last_role = get_last_rsk_role(emp, hist_df)
        last_veh  = get_vehicle_for_role(last_role) if last_role else None
        if last_veh and last_veh in seq:
            emp_vehicle[emp] = seq[(seq.index(last_veh) + 1) % len(seq)]
        else:
            seq_key = tuple(seq)
            count   = _seq_count.get(seq_key, 0)
            emp_vehicle[emp]    = seq[count % len(seq)]
            _seq_count[seq_key] = count + 1

    # OP week: rotate North 1 → South → North 2 daily
    RSK_OP_SEQUENCE = ['North 1', 'South', 'North 2']

    # Forklift week: rotate Hinge 1 → Shuttle → Hinge 2 → Shuttle daily
    # Backstop: never same hinge slot 2 days in a row
    RSK_FORKLIFT_SEQUENCE = ['Hinge 1', 'Shuttle', 'Hinge 2', 'Shuttle']
    RSK_SHUTTLE_ROWS = ['Shuttle 1', 'Shuttle 2', 'Shuttle 3']

    op_emps = sorted([e for e in pool if emp_vehicle.get(e) == 'OP'])
    def starting_op_idx(emp):
        idx = op_emps.index(emp) if emp in op_emps else 0
        return idx % len(RSK_OP_SEQUENCE)

    fl_emps = sorted([e for e in pool if emp_vehicle.get(e) == 'Forklift'])
    def starting_fl_idx(emp):
        idx = fl_emps.index(emp) if emp in fl_emps else 0
        return idx % len(RSK_FORKLIFT_SEQUENCE)

    sh_emps = sorted([e for e in pool if e in rsk['shuttle_qualified']])
    def starting_shuttle_idx(emp):
        idx = sh_emps.index(emp) if emp in sh_emps else 0
        return idx % len(RSK_SHUTTLE_ROWS)

    def get_vehicle_role(emp, day_idx):
        """Get this employee's task for today — stays on their weekly vehicle."""
        vehicle = emp_vehicle.get(emp, 'OP')
        if vehicle == 'OP':
            op_idx = (starting_op_idx(emp) + day_idx) % len(RSK_OP_SEQUENCE)
            return RSK_OP_SEQUENCE[op_idx]
        elif vehicle == 'Forklift':
            can_hinge   = emp in rsk['hinge_qualified']
            can_shuttle = emp in rsk['shuttle_qualified']
            if not can_hinge:
                return 'Shuttle'
            fl_idx = (starting_fl_idx(emp) + day_idx) % len(RSK_FORKLIFT_SEQUENCE)
            role   = RSK_FORKLIFT_SEQUENCE[fl_idx]
            if role == 'Shuttle' and not can_shuttle:
                role = 'Hinge 1' if day_idx % 2 == 0 else 'Hinge 2'
            return role
        else:
            return 'Turret'


    emp_days = {emp: {} for emp in pool}

    for day in DAY_NAMES:
        day_idx   = DAY_NAMES.index(day)
        pto_today = pto_by_day[day]

        # Mark PTO
        rsk_placed = (prefills or {}).get('RSK', {}).get(day, {}).get('placed', set())
        rsk_slots  = (prefills or {}).get('RSK', {}).get(day, {}).get('slots', {})
        avail_today = [e for e in pool if not in_pto(e, pto_today) and not in_pto(e, rsk_placed)]
        for emp in pool:
            if in_pto(emp, pto_today):
                emp_days[emp][day] = 'PTO'
            elif in_pto(emp, rsk_placed):
                emp_days[emp][day] = ''  # leave row blank so prefill stands

        # Compute each person's preferred role from the rotation
        emp_pref = {emp: get_vehicle_role(emp, day_idx) for emp in avail_today}

        # Backstop: no same hinge 2 days in a row
        if day_idx > 0:
            for emp in avail_today:
                role = emp_pref[emp]
                if role in ('Hinge 1', 'Hinge 2'):
                    prev = emp_days[emp].get(DAY_NAMES[day_idx - 1], '')
                    if prev == role:
                        can_shuttle = emp in rsk['shuttle_qualified']
                        emp_pref[emp] = 'Shuttle' if can_shuttle else ('Hinge 2' if role == 'Hinge 1' else 'Hinge 1')

        # Seed slot_to_emp with pre-filled slots so they're treated as taken
        slot_to_emp   = {}
        emp_to_slot   = {}
        shuttle_taken = []
        for label, name in rsk_slots.items():
            slot_to_emp[label] = f'__prefill__{name}'
            if label in RSK_SHUTTLE_ROWS:
                shuttle_taken.append(label)

        # Pass 1: assign each available employee to their preferred slot

        for emp in avail_today:
            pref = emp_pref[emp]
            veh  = emp_vehicle.get(emp, 'OP')

            if veh == 'Turret':
                if 'Turret' not in slot_to_emp:
                    slot_to_emp['Turret'] = emp
                    emp_to_slot[emp]      = 'Turret'

            elif veh == 'OP':
                # Try preferred OP slot, then others in rotation order
                for candidate in ([pref] + [s for s in RSK_OP_SEQUENCE if s != pref]):
                    if candidate not in slot_to_emp:
                        slot_to_emp[candidate] = emp
                        emp_to_slot[emp]        = candidate
                        break

            elif veh == 'Forklift':
                can_hinge   = emp in rsk['hinge_qualified']
                can_shuttle = emp in rsk['shuttle_qualified']
                if pref in ('Shuttle', 'Shuttle 1', 'Shuttle 2', 'Shuttle 3') or not can_hinge:
                    # Assign next available shuttle row in order
                    for row in RSK_SHUTTLE_ROWS:
                        if row not in shuttle_taken:
                            shuttle_taken.append(row)
                            slot_to_emp[row] = emp
                            emp_to_slot[emp]  = row
                            break
                elif pref in ('Hinge 1', 'Hinge 2'):
                    for candidate in ([pref] + [h for h in ('Hinge 1', 'Hinge 2') if h != pref]):
                        if candidate not in slot_to_emp:
                            slot_to_emp[candidate] = emp
                            emp_to_slot[emp]        = candidate
                            break
                    else:
                        # Both hinges taken — try shuttle
                        if can_shuttle:
                            for row in RSK_SHUTTLE_ROWS:
                                if row not in shuttle_taken:
                                    shuttle_taken.append(row)
                                    slot_to_emp[row] = emp
                                    emp_to_slot[emp]  = row
                                    break

        # Pass 2: gap-fill any empty named slots from unassigned qualified employees
        ALL_NAMED = [
            ('Turret',    'turret_qualified'),
            ('Hinge 1',   'hinge_qualified'),
            ('Hinge 2',   'hinge_qualified'),
            ('North 1',   'op_qualified'),
            ('South',     'op_qualified'),
            ('North 2',   'op_qualified'),
            ('Shuttle 1', 'shuttle_qualified'),
            ('Shuttle 2', 'shuttle_qualified'),
            ('Shuttle 3', 'shuttle_qualified'),
        ]
        unassigned = [e for e in avail_today if e not in emp_to_slot]
        for slot, qual_key in ALL_NAMED:
            if slot in slot_to_emp:
                continue
            # Skip if already filled in Week Ahead
            if slot in rsk_slots:
                continue
            candidates = [e for e in unassigned if e in rsk[qual_key]]
            # For Turret gap-fill, prefer emp_vehicle == Turret first
            if slot == 'Turret':
                candidates.sort(key=lambda e: 0 if emp_vehicle.get(e) == 'Turret' else 1)
            if candidates:
                chosen = candidates[0]
                unassigned.remove(chosen)
                slot_to_emp[slot] = chosen
                emp_to_slot[chosen] = slot
                if slot in RSK_SHUTTLE_ROWS and slot not in shuttle_taken:
                    shuttle_taken.append(slot)

        assigned_emps = set(emp_to_slot.keys())
        for emp, slot in emp_to_slot.items():
            emp_days[emp][day] = slot

        for emp in avail_today:
            if emp not in assigned_emps:
                emp_days[emp][day] = 'Extra'

    # Build results
    for emp in pool:
        if is_pto_all_week(emp):
            results.append({'Employee': emp, **{day: 'PTO' for day in DAY_NAMES},
                            'Role': 'Rotating', 'Note': 'Full Week PTO'})
        else:
            days = emp_days.get(emp, {})
            results.append({'Employee': emp,
                            **{day: days.get(day, 'PTO') for day in DAY_NAMES},
                            'Role': 'Rotating', 'Note': ''})

    return pd.DataFrame(results, columns=['Employee'] + DAY_NAMES + ['Role', 'Note'])


# ── RCK Rotation ──────────────────────────────────────────────────────────────

RCK_DEPT      = 'Rack Receiving'
# Rotation cycle: stations 1-6, advanced by one weekly.
# Stations 7 & 8 are RTNR-only (separate dedicated slots).
# Station 9 is overflow — only filled when stations 1-6 are full.
RCK_ROTATION_STATIONS  = [1, 2, 3, 4, 5, 6]
RCK_RTNR_STATIONS      = {7, 8}
RCK_OVERFLOW_STATION   = 9
RCK_ALL_STATIONS       = [1, 2, 3, 4, 5, 6, 7, 8, 9]
RCK_STATION_ROLES = {
    1: 'Station 1', 2: 'Station 2', 3: 'Station 3', 4: 'Station 4', 5: 'Station 5',
    6: 'Station 6', 7: 'Station 7 (.2 RTNR)', 8: 'Station 8 (.8 RTNR)', 9: 'Station 9 (Flex)',
}
RCK_HISTORY = {
    'Rack Checking': ['Rack Checker-'], 'Hinge Checker': ['Hinge Checker-Hinges'],
    'Breakdown': ['Main Breakdown-Hinges'], 'Unload-1': ['Unload-1'],
    'Unload-2': ['Unload-2'], 'Unload-3': ['Unload-3'], 'LTL': ['LTL'], 'House Buy': ['House Buy'],
}
RCK_CT_COLS = {
    'rack_checker': 'PO Checker (RCK)', 'hinge_checker': 'Hinge Checker (HCK)',
    'breakdown': 'Hinge Breakdown (DCK)', 'uld': 'Unload/Aux Shuttle (ULD & SHU)',
    'ltl': 'LTL Desk (LTL)', 'housebuy': 'Housebuys (HB)',
    'rtnr': 'Rack Returns (RTNR)',
}

# Week Ahead labels for confirmations / DNA lookup
RCK_WA_LABEL_ULD1 = 'ULD (5am)- 1'


def load_rck_employees(ct_file: str) -> dict:
    df      = pd.read_excel(ct_file, sheet_name='Cross Training', header=None)
    headers = [str(v).strip() if pd.notna(v) else '' for v in df.iloc[4]]

    def find_col(name):
        for i, h in enumerate(headers):
            if h == name:
                return i
        return None

    name_col  = 4
    alt_col   = 123
    start_col = find_col('Assigned Start Time')
    col_map   = {k: find_col(v) for k, v in RCK_CT_COLS.items()}

    all_names   = []
    name_map    = {}
    start_times = {}
    qualified   = {k: [] for k in RCK_CT_COLS}

    for i in range(5, len(df)):
        area = str(df.iloc[i, 0]).strip() if pd.notna(df.iloc[i, 0]) else ''
        dept = str(df.iloc[i, 1]).strip() if pd.notna(df.iloc[i, 1]) else ''
        name = str(df.iloc[i, name_col]).strip() if pd.notna(df.iloc[i, name_col]) else ''
        alt  = str(df.iloc[i, alt_col]).strip()  if pd.notna(df.iloc[i, alt_col])  else ''
        if area != 'Supply Side' or dept != RCK_DEPT or not name or name == 'nan':
            continue
        all_names.append(name)
        if alt and alt != 'nan':
            name_map[name] = alt
        if start_col is not None:
            val = df.iloc[i, start_col]
            if pd.notna(val):
                try:
                    if hasattr(val, 'hour'):
                        start_times[name] = f"{val.hour}:{val.minute:02d}"
                    else:
                        t = pd.to_datetime(str(val))
                        start_times[name] = f"{t.hour}:{t.minute:02d}"
                except:
                    start_times[name] = str(val).strip()
        for k, col_idx in col_map.items():
            if col_idx is not None:
                val = str(df.iloc[i, col_idx]).strip() if pd.notna(df.iloc[i, col_idx]) else ''
                if val.upper() == 'X':
                    qualified[k].append(name)

    print(f"✓ RCK employees loaded: {len(all_names)} total")
    return {'all': all_names, 'name_map': name_map, 'start_times': start_times, 'qualified': qualified,
            'rtnr': qualified.get('rtnr', [])}


def get_last_rck_role(emp_last_first: str, hist_df: pd.DataFrame, name_map: dict) -> tuple:
    """Return (role, date) of the most recent RCK role from history."""
    first_last = name_map.get(emp_last_first, emp_last_first)
    emp_hist   = hist_df[hist_df['Employee'] == first_last].sort_values('Date', ascending=False)
    for _, row in emp_hist.iterrows():
        for part in row['Raw'].split(','):
            p = part.strip()
            for role, prefixes in RCK_HISTORY.items():
                for prefix in prefixes:
                    if p.startswith(prefix):
                        return role, row['Date']
    return None, None


def get_last_station_rck(emp_last_first: str, hist_df: pd.DataFrame, name_map: dict):
    """Return (station_number, date) of the most recent rack-checking station from history."""
    first_last = name_map.get(emp_last_first, emp_last_first)
    emp_hist   = hist_df[hist_df['Employee'] == first_last].sort_values('Date', ascending=False)
    for _, row in emp_hist.iterrows():
        for part in row['Raw'].split(','):
            p = part.strip()
            if p.startswith('Rack Checker-'):
                try:
                    station = int(p.split('Rack Checker-')[1].split(':')[0])
                    return station, row['Date']
                except:
                    continue
    return None, None


def get_last_unload_date(emp_last_first: str, hist_df: pd.DataFrame, name_map: dict):
    """Return the most recent date this employee did ANY unload role (1, 2, or 3)."""
    first_last = name_map.get(emp_last_first, emp_last_first)
    emp_hist   = hist_df[hist_df['Employee'] == first_last].sort_values('Date', ascending=False)
    unload_prefixes = ['Unload-1', 'Unload-2', 'Unload-3']
    for _, row in emp_hist.iterrows():
        for part in row['Raw'].split(','):
            p = part.strip()
            if any(p.startswith(pfx) for pfx in unload_prefixes):
                return row['Date']
    return None


def did_unload_last_week(emp_last_first: str, hist_df: pd.DataFrame, name_map: dict,
                         week_monday: str) -> bool:
    """Return True if employee did any unload role (1-3) in the week prior to week_monday."""
    from datetime import datetime, timedelta
    try:
        monday = datetime.strptime(week_monday, "%m/%d/%y").date()
    except:
        return False
    prev_monday = monday - timedelta(days=7)
    prev_friday = monday - timedelta(days=3)
    first_last  = name_map.get(emp_last_first, emp_last_first)
    emp_hist    = hist_df[hist_df['Employee'] == first_last].sort_values('Date', ascending=False)
    unload_prefixes = ['Unload-1', 'Unload-2', 'Unload-3']
    for _, row in emp_hist.iterrows():
        if row['Date'] < prev_monday:
            break
        if row['Date'] > prev_friday:
            continue
        for part in row['Raw'].split(','):
            if any(part.strip().startswith(pfx) for pfx in unload_prefixes):
                return True
    return False


def assign_rck(config: dict, pto_by_day: dict, hist_df: pd.DataFrame, prefills: dict = None) -> pd.DataFrame:
    from datetime import date as date_type
    ct_file     = config["ct_file"]
    week_monday = config["schedule_date"]
    do_not_ask  = config.get("do_not_ask", {})
    print("\nLoading RCK data...")
    rck         = load_rck_employees(ct_file)
    all_names   = rck['all']
    name_map    = rck['name_map']
    start_times = rck['start_times']
    qualified   = rck['qualified']
    rtnr_qual   = set(qualified.get('rtnr', []))

    def is_pto_all_week(name):
        return all(in_pto(name, pto_by_day[day]) for day in DAY_NAMES)

    def day_vals_fixed(name, role):
        return {day: 'PTO' if in_pto(name, pto_by_day[day]) else role for day in DAY_NAMES}

    def declines(emp, role_label):
        """Check Confirmations / Do-Not-Ask list for the role."""
        dna = do_not_ask.get(role_label, set())
        return emp in dna or ct_display(emp) in dna or emp.lower() in dna

    results  = []
    assigned = set()

    # ── Fixed shift roles ─────────────────────────────────────────────────────
    ltl = next((e for e in qualified['ltl']
                if e not in assigned and '4:00' in str(start_times.get(e, ''))), None)
    if ltl:
        assigned.add(ltl)
        results.append({'Employee': ltl, **day_vals_fixed(ltl, 'LTL'), 'Role': 'LTL', 'Note': 'LTL (4am)'})

    hb = next((e for e in qualified['housebuy']
               if e not in assigned and '5:30' in str(start_times.get(e, ''))), None)
    if hb:
        assigned.add(hb)
        results.append({'Employee': hb, **day_vals_fixed(hb, 'House Buy'),
                        'Role': 'House Buy', 'Note': 'House Buy (5:30am)'})

    # ── ULD-1: least recently did Unload-1, no back-to-back unload weeks ──────
    # Honor the Confirmations "Do Not Ask" list — never assign declined employees.
    uld1_pool = [e for e in qualified['uld']
                 if e not in assigned and not declines(e, RCK_WA_LABEL_ULD1)]
    uld1_candidates = [e for e in uld1_pool
                       if not did_unload_last_week(e, hist_df, name_map, week_monday)]
    if not uld1_candidates:
        uld1_candidates = list(uld1_pool)
    if uld1_candidates:
        def uld1_score(emp):
            # Find the most recent date they specifically did Unload-1
            first_last = name_map.get(emp, emp)
            emp_hist   = hist_df[hist_df['Employee'] == first_last].sort_values('Date', ascending=False)
            for _, row in emp_hist.iterrows():
                for part in row['Raw'].split(','):
                    if part.strip().startswith('Unload-1'):
                        return row['Date']  # most recent Unload-1 date — higher = deprioritized
            return date_type(2000, 1, 1)  # never done it — highest priority
        uld1 = min(uld1_candidates, key=uld1_score)
        assigned.add(uld1)
        results.append({'Employee': uld1, **day_vals_fixed(uld1, 'ULD-1'), 'Role': 'ULD-1', 'Note': 'ULD-1'})

    # ── Exclude pre-placed from Week Ahead ───────────────────────────────────
    rck_all_placed = set()
    for day in DAY_NAMES:
        rck_all_placed.update((prefills or {}).get('RCK', {}).get(day, {}).get('placed', set()))
    checker_pool = [e for e in qualified['rack_checker']
                    if e not in assigned and not in_pto(e, rck_all_placed)]

    # ── Helpers ───────────────────────────────────────────────────────────────
    def pick_for_special(role, qual_key, exclude):
        """Pick trained person who hasn't done this role in longest."""
        candidates = [e for e in checker_pool if e not in exclude]
        if qual_key:
            candidates = [e for e in candidates if e in qualified[qual_key]]
        if not candidates:
            return None
        def score(emp):
            last_r, last_d = get_last_rck_role(emp, hist_df, name_map)
            if last_r == role: return pd.Timestamp('2099-01-01').date()
            return last_d if last_d else date_type(2000, 1, 1)
        return min(candidates, key=score)

    def pick_for_uld(role, exclude):
        """Pick ULD-2/3: longest since any unload (1-3), block back-to-back weeks."""
        candidates = [e for e in qualified['uld'] if e not in exclude]
        no_recent  = [e for e in candidates
                      if not did_unload_last_week(e, hist_df, name_map, week_monday)]
        candidates = no_recent if no_recent else candidates
        if not candidates:
            return None
        def score(emp):
            last_d = get_last_unload_date(emp, hist_df, name_map)
            return last_d if last_d else date_type(2000, 1, 1)
        return min(candidates, key=score)

    special_assigned = set(assigned)
    emp_role_map     = {}

    # Hinge Checker, Breakdown
    for role, qual_key in [('Hinge Checker', 'hinge_checker'), ('Breakdown', 'breakdown')]:
        emp = pick_for_special(role, qual_key, special_assigned)
        if emp:
            special_assigned.add(emp)
            emp_role_map[emp] = role

    # ULD-2, ULD-3
    for role in ['Unload-2', 'Unload-3']:
        emp = pick_for_uld(role, special_assigned)
        if emp:
            special_assigned.add(emp)
            emp_role_map[emp] = role

    # ── Station assignment: Hungarian on stations 1-9 ────────────────────────
    # Cost layout:
    #   Stations 1-6 — rotation cycle (1→2→…→6→1). Cost = forward distance;
    #                  500 if same station as last week.
    #   Stations 7-8 — RTNR-only. Cost 1 if RTNR-qualified (and not same as
    #                  last week, else 500); 998 if not RTNR (blocks assignment).
    #   Station 9   — overflow, only used when stations 1-6 are full. Cost 700.
    #   Padded slot — no real station available, becomes Extra. Cost 900.
    station_emps = [e for e in checker_pool if e not in emp_role_map]

    def is_rtnr(emp):
        return emp in rtnr_qual or ct_display(emp) in rtnr_qual

    if station_emps:
        n_emps  = len(station_emps)
        padded  = list(RCK_ALL_STATIONS) + [None] * max(0, n_emps - len(RCK_ALL_STATIONS))
        cost    = np.zeros((n_emps, len(padded)))

        for i, emp in enumerate(station_emps):
            last_sta, _ = get_last_station_rck(emp, hist_df, name_map)
            for j, sta in enumerate(padded):
                if sta is None:
                    cost[i, j] = 900  # padded → Extra
                elif sta == RCK_OVERFLOW_STATION:
                    cost[i, j] = 700  # overflow — only used when 1-6 full
                elif sta in RCK_RTNR_STATIONS:
                    if not is_rtnr(emp):
                        cost[i, j] = 998  # blocked: not RTNR-qualified
                    else:
                        # Prefer 7/8 for RTNR people (cost 0) but force swap if they
                        # were there last week (cost 500 keeps them off the same station).
                        cost[i, j] = 500 if last_sta == sta else 0
                elif sta in RCK_ROTATION_STATIONS:
                    # Forward cyclic rotation 1→2→3→4→5→6→1
                    if last_sta in RCK_ROTATION_STATIONS:
                        li   = RCK_ROTATION_STATIONS.index(last_sta)
                        ci   = RCK_ROTATION_STATIONS.index(sta)
                        dist = (ci - li) % len(RCK_ROTATION_STATIONS)
                        cost[i, j] = 500 if dist == 0 else dist
                    else:
                        cost[i, j] = 1  # no history, or came from 7/8/9 — fresh start
                else:
                    cost[i, j] = 1

        row_ind, col_ind = linear_sum_assignment(cost)
        emp_to_station   = {station_emps[i]: padded[j] for i, j in zip(row_ind, col_ind)}

        for emp in station_emps:
            sta = emp_to_station.get(emp)
            if sta is None:
                emp_role_map[emp] = 'Extra'
            else:
                emp_role_map[emp] = RCK_STATION_ROLES[sta]

    # ── Build results ─────────────────────────────────────────────────────────
    for emp in checker_pool:
        display_role = emp_role_map.get(emp, 'Extra')
        if is_pto_all_week(emp):
            results.append({'Employee': emp, **{day: 'PTO' for day in DAY_NAMES},
                            'Role': display_role, 'Note': 'Full Week PTO'})
        else:
            results.append({'Employee': emp, **day_vals_fixed(emp, display_role),
                            'Role': display_role, 'Note': ''})

    covered = assigned | set(checker_pool)
    for emp in all_names:
        if emp not in covered:
            results.append({'Employee': emp,
                            **{day: 'PTO' if in_pto(emp, pto_by_day[day]) else '— Unassigned —' for day in DAY_NAMES},
                            'Role': '', 'Note': 'Not in any pool'})

    return pd.DataFrame(results, columns=['Employee'] + DAY_NAMES + ['Role', 'Note'])


# ── AUX Rotation ──────────────────────────────────────────────────────────────

AUX_DEPTS = ['Aux Rack Receiving', 'Aux Rack Stockkeeping']
AUX_ROLES = ['Checker', 'Material Handler', 'Wide Aisle', 'Turret', 'Shuttle/Transport']
AUX_CT_COLS = {
    'Checker': 'Aux Checking (AXC)', 'Material Handler': 'AUX Material Handler (AXD)',
    'Wide Aisle': 'AUX Wide Aisle (AXS)', 'Turret': 'AUX Turret (AXS)',
    'Shuttle/Transport': 'AUX Transport (AXS)',
}


def load_aux_employees(ct_file: str) -> dict:
    df      = pd.read_excel(ct_file, sheet_name='Cross Training', header=None)
    headers = [str(v).strip() if pd.notna(v) else '' for v in df.iloc[4]]

    def find_col(name):
        for i, h in enumerate(headers):
            if h == name:
                return i
        return None

    name_col  = 4
    alt_col   = 123
    col_map   = {role: find_col(col) for role, col in AUX_CT_COLS.items()}
    all_names = []
    name_map  = {}
    qualified = {role: [] for role in AUX_ROLES}

    for i in range(5, len(df)):
        area = str(df.iloc[i, 0]).strip() if pd.notna(df.iloc[i, 0]) else ''
        dept = str(df.iloc[i, 1]).strip() if pd.notna(df.iloc[i, 1]) else ''
        name = str(df.iloc[i, name_col]).strip() if pd.notna(df.iloc[i, name_col]) else ''
        alt  = str(df.iloc[i, alt_col]).strip()  if pd.notna(df.iloc[i, alt_col])  else ''
        if area != 'Supply Side' or dept not in AUX_DEPTS or not name or name == 'nan':
            continue
        all_names.append(name)
        if alt and alt != 'nan':
            name_map[name] = alt
        for role, col_idx in col_map.items():
            if col_idx is not None:
                val = str(df.iloc[i, col_idx]).strip() if pd.notna(df.iloc[i, col_idx]) else ''
                if val.upper() == 'X':
                    qualified[role].append(name)

    print(f"✓ AUX employees loaded: {len(all_names)} total")
    return {'all': all_names, 'name_map': name_map, 'qualified': qualified}


def assign_aux(config: dict, pto_by_day: dict, prefills: dict = None) -> pd.DataFrame:
    ct_file   = config["ct_file"]
    print("\nLoading AUX employees...")
    aux       = load_aux_employees(ct_file)
    all_names = aux['all']
    qualified = aux['qualified']

    def is_pto_all_week(name):
        return all(in_pto(name, pto_by_day[day]) for day in DAY_NAMES)

    # Deterministic per-week shuffle of employee order. Removes the alphabetical
    # tiebreak bias where the same person always got 3 days of a role and the
    # other got 2 — now the 3-vs-2 split flips week to week.
    rng = random.Random(f"AUX-{config['schedule_date']}")
    name_order = list(all_names)
    rng.shuffle(name_order)

    # Track how many times each employee has had each role this week
    role_count = {emp: {role: 0 for role in AUX_ROLES} for emp in all_names}
    emp_days   = {emp: {} for emp in all_names}

    for day in DAY_NAMES:
        pto_today   = pto_by_day[day]
        aux_placed  = (prefills or {}).get('AUX', {}).get(day, {}).get('placed', set())
        avail_today = [e for e in name_order if not in_pto(e, pto_today) and not in_pto(e, aux_placed)]
        day_idx     = DAY_NAMES.index(day)

        assigned_today = {}

        aux_slots = (prefills or {}).get('AUX', {}).get(day, {}).get('slots', {})
        # Map Week Ahead label back to AUX role
        AUX_LABEL_TO_ROLE = {v: k for k, v in {
            'Checker': 'Checker (AXC)', 'Material Handler': 'Material Handler (AXD)',
            'Shuttle/Transport': 'Shuttle/Transport (AXS)', 'Wide Aisle': 'Wide Aisle/Transport (AXS)',
            'Turret': 'Turret (AXS)',
        }.items()}
        prefilled_aux_roles = {AUX_LABEL_TO_ROLE.get(lbl, lbl) for lbl in aux_slots}

        # Use Hungarian algorithm to assign roles optimally each day:
        # - strongly penalize repeating the same role this week
        # - extra penalty for same role as yesterday
        # - unqualified = 9999 (forbidden)
        open_roles = [r for r in AUX_ROLES if r not in prefilled_aux_roles]
        avail_emps = list(avail_today)  # already shuffled per-week, excludes PTO/placed

        if avail_emps and open_roles:
            import numpy as np
            from scipy.optimize import linear_sum_assignment
            n_emps  = len(avail_emps)
            n_roles = len(open_roles)
            # Pad to square if needed
            size = max(n_emps, n_roles)
            cost = np.full((size, size), 0.0)
            for i, emp in enumerate(avail_emps):
                for j, role in enumerate(open_roles):
                    if emp not in qualified[role]:
                        cost[i, j] = 9999
                        continue
                    c = 0
                    c += role_count[emp][role] * 200          # repeat penalty
                    if day_idx > 0 and emp_days[emp].get(DAY_NAMES[day_idx-1]) == role:
                        c += 500                               # yesterday penalty
                    cost[i, j] = c
            row_ind, col_ind = linear_sum_assignment(cost)
            for i, j in zip(row_ind, col_ind):
                if i < n_emps and j < n_roles and cost[i, j] < 9999:
                    emp  = avail_emps[i]
                    role = open_roles[j]
                    assigned_today[emp]  = role
                    role_count[emp][role] += 1

        for emp in avail_today:
            emp_days[emp][day] = assigned_today.get(emp, '— Unassigned —')
        for emp in all_names:
            if in_pto(emp, pto_today):
                emp_days[emp][day] = 'PTO'
            elif in_pto(emp, aux_placed):
                emp_days[emp][day] = ''  # leave row blank — prefill handles it

    results = []
    for emp in all_names:
        if is_pto_all_week(emp):
            results.append({'Employee': emp, **{day: 'PTO' for day in DAY_NAMES}, 'Note': 'Full Week PTO'})
        else:
            days = emp_days.get(emp, {})
            results.append({'Employee': emp, **{day: days.get(day, 'PTO') for day in DAY_NAMES}, 'Note': ''})

    return pd.DataFrame(results, columns=['Employee'] + DAY_NAMES + ['Note'])



# ── MC (Material Control) ─────────────────────────────────────────────────────

MC_DEPT  = 'Material Control'
MC_SLOTS = ['MC1', 'MC2', 'MC3', 'MC4', 'MC5', 'MC6', 'MC7', 'MC8']


def assign_mc(config: dict, pto_by_day: dict, prefills: dict = None) -> pd.DataFrame:
    """
    Assigns MC employees to fixed weekly slots MC1-MC8.
    Employees are sorted alphabetically and assigned in order — no rotation.
    PTO/Extra handled same as other depts.
    """
    ct_file = config["ct_file"]
    df      = pd.read_excel(ct_file, sheet_name='Cross Training', header=None)

    employees = []
    for i in range(5, len(df)):
        area = str(df.iloc[i, 0]).strip() if pd.notna(df.iloc[i, 0]) else ''
        dept = str(df.iloc[i, 1]).strip() if pd.notna(df.iloc[i, 1]) else ''
        name = str(df.iloc[i, 4]).strip() if pd.notna(df.iloc[i, 4]) else ''
        if area == 'Supply Side' and dept == MC_DEPT and name and name != 'nan':
            employees.append(name)

    employees = sorted(employees)
    print(f"✓ MC employees loaded: {len(employees)} total")

    # Pre-placement awareness: if someone is pre-placed anywhere in MC this week,
    # skip them from the alphabetical slot assignment so they only appear in the prefilled cell.
    mc_all_placed = set()
    for day in DAY_NAMES:
        mc_all_placed.update((prefills or {}).get('MC', {}).get(day, {}).get('placed', set()))

    def is_pto_all_week(name):
        return all(in_pto(name, pto_by_day[day]) for day in DAY_NAMES)

    results = []
    slot_idx = 0
    for emp in employees:
        if in_pto(emp, mc_all_placed):
            # User has them placed somewhere already — don't double-assign.
            continue
        slot = MC_SLOTS[slot_idx] if slot_idx < len(MC_SLOTS) else f'MC{slot_idx+1}'
        slot_idx += 1
        if is_pto_all_week(emp):
            results.append({'Employee': emp, **{day: 'PTO' for day in DAY_NAMES},
                            'Slot': slot, 'Note': 'Full Week PTO'})
        else:
            day_vals = {}
            for day in DAY_NAMES:
                pto_set = pto_by_day[day]
                placed_today = (prefills or {}).get('MC', {}).get(day, {}).get('placed', set())
                if ct_display(emp) in pto_set or emp in pto_set:
                    day_vals[day] = 'PTO'
                elif in_pto(emp, placed_today):
                    day_vals[day] = ''  # already placed today — leave blank
                else:
                    day_vals[day] = slot
            results.append({'Employee': emp, **day_vals, 'Slot': slot, 'Note': ''})

    return pd.DataFrame(results, columns=['Employee'] + DAY_NAMES + ['Slot', 'Note'])

# ── IAG codings ───────────────────────────────────────────────────────────────

def load_all_start_times(ct_file: str) -> dict:
    """Map every employee to their assigned start time as 'HH:MM', from the
    Cross Training Log's 'Assigned Start Time' column. Keyed by both the
    'Last, First' (col E) and 'First Last' (col DT) forms, plus lowercase, so a
    Week Ahead display name can always be matched back to a shift time."""
    import re
    out = {}
    try:
        df = pd.read_excel(ct_file, sheet_name='Cross Training', header=None)
    except Exception as e:
        print(f"  ⚠ Could not read start times from CT log: {e}")
        return out

    headers   = [str(v).strip() if pd.notna(v) else '' for v in df.iloc[4]]
    start_col = next((i for i, h in enumerate(headers)
                      if 'Assigned Start Time' in h or 'Start Time' in h), None)
    if start_col is None:
        return out
    name_col, alt_col = 4, 123

    def fmt(val):
        try:
            if hasattr(val, 'hour'):
                return f"{val.hour:02d}:{val.minute:02d}"
            t = pd.to_datetime(str(val))
            return f"{t.hour:02d}:{t.minute:02d}"
        except Exception:
            m = re.match(r'^(\d{1,2}):(\d{2})', str(val).strip())
            return f"{int(m.group(1)):02d}:{m.group(2)}" if m else None

    for i in range(5, len(df)):
        val = df.iloc[i, start_col]
        if pd.isna(val):
            continue
        t = fmt(val)
        if not t:
            continue
        col_e  = str(df.iloc[i, name_col]).strip() if pd.notna(df.iloc[i, name_col]) else ''
        col_dt = str(df.iloc[i, alt_col]).strip()  if pd.notna(df.iloc[i, alt_col])  else ''
        for key in (col_e, col_dt):
            if key and key != 'nan':
                out[key]         = t
                out[key.lower()] = t
    return out


# IAG role labels (as they appear in col A of the IAG block), lowercased for matching.
IAG_ROLE_LABELS = {
    'desk/ macro', 'racks', 'bins 1', 'bins 2', 'bins 3',
    'floater/1st floor', 'float/audits', 'counts/material found',
}


def update_iag_codings(wb, ws_names, config: dict):
    """Rewrite the IAG codings in the 'Codings' sheet so each role's embedded
    shift time matches the actual start time (from the CT log) of whoever is
    placed in that role in the Week Ahead. The coding prefix (IAG / Counts) is
    preserved — only the time changes, e.g. IAG09:30 → IAG08:30."""
    import re
    if 'Codings' not in wb.sheetnames:
        print("  ⚠ No 'Codings' sheet — skipping IAG coding update")
        return
    ws_cod = wb['Codings']

    IAG_COL  = 22  # DEPT_COL_START['IAG']
    DAY_COLS = {'Monday': 23, 'Tuesday': 24, 'Wednesday': 25, 'Thursday': 26, 'Friday': 27}

    start_times = load_all_start_times(config.get('ct_file', ''))
    if not start_times:
        print("  ⚠ No start times available — IAG codings left as-is")
        return

    def lookup_time(name):
        if not name:
            return None
        name = str(name).strip()
        for key in (name, name.lower(), ct_display(name), str(ct_display(name)).lower()):
            if key in start_times:
                return start_times[key]
        return None

    # Who's in each IAG role, per day, from the names sheet we just wrote.
    names_by_label = {}
    for r in range(2, ws_names.max_row + 1):
        lbl = ws_names.cell(row=r, column=IAG_COL).value
        if lbl is None:
            continue
        key = str(lbl).strip().lower()
        if key not in IAG_ROLE_LABELS:
            continue
        names_by_label[key] = {day: ws_names.cell(row=r, column=col).value
                               for day, col in DAY_COLS.items()}

    updated = 0
    for r in range(2, ws_cod.max_row + 1):
        lbl = ws_cod.cell(row=r, column=IAG_COL).value
        if lbl is None:
            continue
        key = str(lbl).strip().lower()
        if key not in IAG_ROLE_LABELS or key not in names_by_label:
            continue
        for day, col in DAY_COLS.items():
            t = lookup_time(names_by_label[key].get(day))
            if not t:
                continue  # nobody placed (or no start time) — keep the existing coding
            cell    = ws_cod.cell(row=r, column=col)
            current = str(cell.value) if cell.value is not None else ''
            m       = re.match(r'^([^\d]*)', current)
            prefix  = m.group(1) if (m and m.group(1)) else ('Counts' if key.startswith('counts') else 'IAG')
            new_val = f"{prefix}{t}"
            if new_val != current:
                cell.value = new_val
                updated += 1
    print(f"  ✓ IAG codings synced to assigned shift times ({updated} cell(s) updated)")


# ── Write to Week Ahead ───────────────────────────────────────────────────────

def write_week_ahead(assignments: dict, config: dict, leave_by_day: dict = None, prefills: dict = None):
    """
    Writes all dept assignments into Week Ahead.xlsx.
    Each dept block has named role rows, then Extra rows, TRN rows, PTO rows.
    Every employee appears exactly once per dept per day.
    """
    dest = config["week_ahead"]

    # Read prefills from the live file RIGHT NOW before clearing anything
    if prefills is None:
        prefills = load_week_ahead_prefills(config)

    wb   = load_workbook(dest, keep_links=True)
    ws   = wb['Week Ahead']

    DEPT_COL_START = {'BCK': 1, 'MC': 8, 'BSK': 15, 'IAG': 22, 'RCK': 29, 'RSK': 36, 'AUX': 43}
    DAY_OFFSETS    = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5}

    # Read all row labels per dept (col A of each dept block)
    max_row = ws.max_row
    dept_row_index = {}  # {dept: {label: [row_numbers]}}
    for dept, col_start in DEPT_COL_START.items():
        label_rows = {}
        for r in range(2, max_row + 1):
            cell = ws.cell(row=r, column=col_start)
            if cell.value is not None:
                lbl = str(cell.value).strip()
                label_rows.setdefault(lbl, []).append(r)
        dept_row_index[dept] = label_rows

    # Per-(dept, day) name set — guarantees each name appears at most once in a column
    column_names = {(dept, day): set() for dept in DEPT_COL_START for day in DAY_NAMES}

    def _col_names_lower(dept, day):
        return {n.lower() for n in column_names[(dept, day)]}

    def name_already_in_column(dept, day, name) -> bool:
        return name and name.lower() in _col_names_lower(dept, day)

    def write_cell(dept, label, day, value, occurrence=0):
        """Write value into the cell for dept/label/day. occurrence picks which row if label repeats."""
        rows = dept_row_index[dept].get(label, [])
        if not rows or occurrence >= len(rows):
            return False
        row = rows[occurrence]
        col = DEPT_COL_START[dept] + DAY_OFFSETS[day]
        if ws.cell(row=row, column=col).value is not None:
            return False
        if name_already_in_column(dept, day, str(value)):
            return False
        ws.cell(row=row, column=col).value = value
        column_names[(dept, day)].add(str(value))
        return True

    # Build set of cells to protect from clearing:
    # (1) any cell that currently has a value (per-cell, not per-row) — protects pre-fills
    PROTECT_LABELS    = {'Extra', 'TRN', 'PTO', 'Other'}
    prefill_protected_cells = set()  # {(row, col)} that already contain a value at read-time
    for dept, col_start in DEPT_COL_START.items():
        for label, rows in dept_row_index[dept].items():
            for day, day_off in DAY_OFFSETS.items():
                col = col_start + day_off
                for r in rows:
                    v = ws.cell(row=r, column=col).value
                    if v is not None:
                        prefill_protected_cells.add((r, col))
                        # Seed column_names so we never double-write the same person in a column
                        column_names[(dept, day)].add(str(v).strip())

    # Clear writeable cells — but protect any cell that currently has a value
    for dept in DEPT_COL_START:
        for day in DAY_NAMES:
            for label, rows in dept_row_index[dept].items():
                col = DEPT_COL_START[dept] + DAY_OFFSETS[day]
                for r in rows:
                    if (r, col) in prefill_protected_cells:
                        continue  # leave pre-filled cell alone
                    ws.cell(row=r, column=col).value = None

    IAG_LABEL_MAP = {
        'Desk': 'Desk/ Macro', 'Float/Audits': 'Float/Audits',
        'Counts': 'Counts/Material Found',
    }
    RCK_LABEL_MAP = {
        'LTL': 'LTL (4am)', 'House Buy': 'ULD/HB (5:30am)',
        'ULD-1': 'ULD (5am)- 1', 'Unload-2': 'ULD-2',
        'Unload-3': 'ULD (ULD/Extra)-3',
    }
    AUX_LABEL_MAP = {
        'Checker':           'Checker (AXC)',
        'Material Handler':  'Material Handler (AXD)',
        'Shuttle/Transport': 'Shuttle/Transport (AXS)',
        'Wide Aisle':        'Wide Aisle/Transport (AXS)',
        'Turret':            'Turret (AXS)',
    }

    # Build set of employees on leave for each day — skip from PTO section
    on_leave_any_day = set()
    if leave_by_day:
        for day_set in leave_by_day.values():
            on_leave_any_day.update(day_set)

    def classify_day(dept, cv_str, note, role):
        """Returns 'assigned', 'pto', 'trn', 'extra', or 'skip'."""
        if cv_str == '':
            return 'skip'  # explicitly blank — already handled by a prefill, do not overflow-write
        is_pto = cv_str == 'PTO' or (cv_str.startswith('PTO') and '→' in cv_str)
        if is_pto:
            return 'pto'
        if cv_str == 'Training' or (dept == 'BSK' and note == 'In Training'):
            return 'trn'
        if cv_str in ('Extra', '— Unassigned —'):
            return 'extra'
        return 'assigned'

    unplaced = []  # (dept, day, emp, section) — for end-of-run summary

    def write_assigned_day(dept, cv_str, note, role, day, emp, floater_counters):
        """Write a single assigned day cell for an employee. Returns True if written."""
        col_start  = DEPT_COL_START[dept]
        day_offset = DAY_OFFSETS[day]

        # Global dedup: if this name is already in the column for this day, do not write again
        if name_already_in_column(dept, day, emp):
            return True  # already represented — consider handled

        if dept == 'BCK':
            try:
                station = int(float(cv_str))
                return write_cell('BCK', f'Station {station}', day, emp)
            except:
                return False

        elif dept == 'MC':
            if cv_str in MC_SLOTS and dept_row_index['MC'].get(cv_str):
                return write_cell('MC', cv_str, day, emp)
            return False

        elif dept == 'BSK':
            if cv_str == 'Floater':
                float_labels = ['1st Floor Float', '2nd Floor Float', '3rd Floor Float']
                fi = floater_counters.get(day, 0)
                while fi < len(float_labels):
                    if write_cell('BSK', float_labels[fi], day, emp):
                        floater_counters[day] = fi + 1
                        return True
                    fi += 1
                floater_counters[day] = fi
                return False
            elif cv_str == 'Sizer' or note == 'Sizer':
                return write_cell('BSK', 'Sizer', day, emp)
            elif cv_str in BSK_ROTATION:
                return write_cell('BSK', cv_str, day, emp)
            return False

        elif dept == 'IAG':
            label = IAG_LABEL_MAP.get(cv_str, cv_str)
            if note.startswith('Desk'):
                label = 'Desk/ Macro'
            if dept_row_index['IAG'].get(label):
                return write_cell('IAG', label, day, emp)
            return False

        elif dept == 'RCK':
            label = RCK_LABEL_MAP.get(role, RCK_LABEL_MAP.get(cv_str, cv_str))
            if dept_row_index['RCK'].get(label):
                return write_cell('RCK', label, day, emp)
            return False

        elif dept == 'RSK':
            RSK_SHUTTLE_ROWS = ['Shuttle 1', 'Shuttle 2', 'Shuttle 3']
            RSK_WKD_ROWS     = ['WKD 1', 'WKD 2']
            if cv_str in ('Shuttle 1', 'Shuttle 2', 'Shuttle 3'):
                preferred = [cv_str] + [r for r in RSK_SHUTTLE_ROWS if r != cv_str]
                col = col_start + day_offset
                for lbl in preferred:
                    rows = dept_row_index['RSK'].get(lbl, [])
                    for r in rows:
                        if (r, col) in prefill_protected_cells:
                            continue
                        if ws.cell(row=r, column=col).value is None:
                            if name_already_in_column(dept, day, emp):
                                return True
                            ws.cell(row=r, column=col).value = emp
                            column_names[(dept, day)].add(emp)
                            return True
                return False
            elif cv_str == 'WKD' or role == 'WKD':
                col = col_start + day_offset
                for lbl in RSK_WKD_ROWS:
                    rows = dept_row_index['RSK'].get(lbl, [])
                    for r in rows:
                        if (r, col) in prefill_protected_cells:
                            continue
                        if ws.cell(row=r, column=col).value is None:
                            if name_already_in_column(dept, day, emp):
                                return True
                            ws.cell(row=r, column=col).value = emp
                            column_names[(dept, day)].add(emp)
                            return True
                return False
            else:
                label = cv_str if dept_row_index['RSK'].get(cv_str) else role
                if dept_row_index['RSK'].get(label):
                    return write_cell('RSK', label, day, emp)
                return False

        elif dept == 'AUX':
            label = AUX_LABEL_MAP.get(cv_str, cv_str)
            if dept_row_index['AUX'].get(label):
                return write_cell('AUX', label, day, emp)
            return False

        return False

    # ── Write each dept ───────────────────────────────────────────────────────
    for dept, df in assignments.items():
        if df is None:
            continue

        floater_counters = {day: 0 for day in DAY_NAMES}

        emp_day_class = {}
        for _, row in df.iterrows():
            emp = str(row.get('Employee', '')).strip()
            if not emp or emp.startswith('—'):
                continue
            note = str(row.get('Note', '')).strip()
            role = str(row.get('Role', '')).strip()
            day_classes = {}
            for day in DAY_NAMES:
                cv     = row.get(day)
                cv_str = str(cv).strip() if cv is not None else ''
                day_classes[day] = classify_day(dept, cv_str, note, role)
            emp_day_class[emp] = day_classes

        # ── Pass 1: write assigned days into their named role rows ────────────
        for _, row in df.iterrows():
            emp = str(row.get('Employee', '')).strip()
            if not emp or emp.startswith('—'):
                continue
            note = str(row.get('Note', '')).strip()
            role = str(row.get('Role', '')).strip()
            for day in DAY_NAMES:
                cv     = row.get(day)
                cv_str = str(cv).strip() if cv is not None else ''
                if emp_day_class[emp][day] == 'assigned':
                    placed = write_assigned_day(dept, cv_str, note, role, day,
                                                ct_display(emp), floater_counters)
                    if not placed:
                        # Their named slot was full / missing / already taken (e.g. more
                        # people than slots, or a duplicate role). Never let them fall off
                        # the schedule — reclassify as Extra so Pass 2 writes them to the
                        # Extra row. This applies to every department.
                        emp_day_class[emp][day] = 'extra'

        # ── Pass 2: write overflow rows (PTO / TRN / Extra) ──────────────────
        def find_row_for_days(dept, section_label, days_needed):
            """Prefer a fully empty row; only share if no empty row exists."""
            rows      = dept_row_index[dept].get(section_label, [])
            col_start = DEPT_COL_START[dept]
            # First pass: find a completely empty row (all 5 days free)
            for r in rows:
                if all(ws.cell(row=r, column=col_start + DAY_OFFSETS[d]).value is None for d in DAY_NAMES):
                    return r
            # Second pass: find a row where at least the needed days are free
            for r in rows:
                if all(ws.cell(row=r, column=col_start + DAY_OFFSETS[d]).value is None for d in days_needed):
                    return r
            return None

        for _, row in df.iterrows():
            emp = str(row.get('Employee', '')).strip()
            if not emp or emp.startswith('—'):
                continue
            note = str(row.get('Note', '')).strip()
            role = str(row.get('Role', '')).strip()
            classes = emp_day_class[emp]

            days_by_class = {c: [d for d in DAY_NAMES if classes[d] == c]
                             for c in ('pto', 'trn', 'extra')}

            has_overflow = any(days_by_class[c] for c in ('pto', 'trn', 'extra'))
            if not has_overflow:
                continue

            # Skip leave employees from Week Ahead overflow sections
            if in_pto(emp, on_leave_any_day):
                continue

            col_start = DEPT_COL_START[dept]
            display_emp = ct_display(emp)
            for section, section_days in [('PTO', days_by_class['pto']),
                                           ('TRN', days_by_class['trn']),
                                           ('Extra', days_by_class['extra'])]:
                if not section_days:
                    continue
                # Filter out days where this person is already in the column from a prefill or pass 1
                section_days = [d for d in section_days
                                if not name_already_in_column(dept, d, display_emp)]
                if not section_days:
                    continue
                target_row = find_row_for_days(dept, section, section_days)
                if target_row is None:
                    print(f"  ⚠ No {section} row available for {display_emp} in {dept} ({', '.join(section_days)})")
                    for d in section_days:
                        unplaced.append((dept, d, display_emp, section))
                    continue
                for day in section_days:
                    col = col_start + DAY_OFFSETS[day]
                    if (target_row, col) in prefill_protected_cells:
                        continue
                    if ws.cell(row=target_row, column=col).value is not None:
                        continue
                    if name_already_in_column(dept, day, display_emp):
                        continue
                    ws.cell(row=target_row, column=col).value = display_emp
                    column_names[(dept, day)].add(display_emp)

    # Sync IAG codings to the actual assigned shift times of who's placed where
    try:
        update_iag_codings(wb, ws, config)
    except Exception as e:
        print(f"  ⚠ IAG coding update skipped: {e}")

    wb.save(dest)
    print(f"\n✓ Week Ahead updated: {dest}")
    if unplaced:
        print(f"\n⚠ {len(unplaced)} employee-days could not be placed (insufficient rows):")
        from collections import defaultdict
        by_dept = defaultdict(list)
        for dept, day, emp, section in unplaced:
            by_dept[(dept, section)].append(f"{emp} ({day})")
        for (dept, section), items in sorted(by_dept.items()):
            print(f"  {dept} / {section}: {', '.join(items)}")
        print("  → Add more rows to the affected sections in Week Ahead Template.")
    print("  Review and edit as needed, then run Supply Side Schedule Writer.py")


# ── Main ──────────────────────────────────────────────────────────────────────

class SupplySideScheduling(Tool):
    name = "supply_side_scheduling"
    description = """
    Generates weekly Supply Side workforce assignments for all departments
    (BCK, MC, BSK, IAG, RSK, RCK, AUX) and writes them to Week Ahead.xlsx for review.
    No inputs required — reads all configuration from Inputs.xlsx.
    """
    param_spec = {}

    def run(self, params):
        config       = load_config()
        supply_names = load_supply_side_employees(config["ct_file"])
        hist_df      = load_historical_tasks(config["historical_file"], supply_names)
        pto_by_day, leave_by_day = load_week_pto(config["week_dates"])

        prefills = load_week_ahead_prefills(config)

        assignments = {}
        assignments['BCK'] = assign_bin_checking(hist_df, config, pto_by_day, prefills)
        assignments['MC']  = assign_mc(config, pto_by_day, prefills)
        assignments['BSK'] = assign_bin_stockkeeping(config, pto_by_day, hist_df, prefills)
        assignments['IAG'] = assign_iag(config, pto_by_day, hist_df, prefills)
        assignments['RSK'] = assign_rsk(config, pto_by_day, hist_df, prefills)
        assignments['RCK'] = assign_rck(config, pto_by_day, hist_df, prefills)
        assignments['AUX'] = assign_aux(config, pto_by_day, prefills)

        write_week_ahead(assignments, config, leave_by_day, prefills)

        return [{"status": "done", "week_of": config["schedule_date"]}], params


if __name__ == '__main__':
    print("=" * 70)
    print("SUPPLY SIDE SCHEDULING — Step 1: Generate & Write to Week Ahead")
    print("=" * 70)

    config       = load_config()
    supply_names = load_supply_side_employees(config["ct_file"])
    hist_df      = load_historical_tasks(config["historical_file"], supply_names)

    print("\nLoading PTO for full week...")
    pto_by_day, leave_by_day = load_week_pto(config["week_dates"])

    prefills = load_week_ahead_prefills(config)

    assignments = {}
    assignments['BCK'] = assign_bin_checking(hist_df, config, pto_by_day, prefills)
    assignments['MC']  = assign_mc(config, pto_by_day, prefills)
    assignments['BSK'] = assign_bin_stockkeeping(config, pto_by_day, hist_df, prefills)
    assignments['IAG'] = assign_iag(config, pto_by_day, hist_df, prefills)
    assignments['RSK'] = assign_rsk(config, pto_by_day, hist_df, prefills)
    assignments['RCK'] = assign_rck(config, pto_by_day, hist_df, prefills)
    assignments['AUX'] = assign_aux(config, pto_by_day, prefills)

    for dept, df in assignments.items():
        print(f"\n{'='*60}\n{dept} — Week of {config['schedule_date']}\n{'='*60}")
        print(df.to_string(index=False))
        if 'Distance' in df.columns:
            numeric_dist = df['Distance'].dropna().astype(float)
            if not numeric_dist.empty:
                print(f"\n  Total rotation distance: {int(numeric_dist.sum())}  |  "
                      f"Avg: {numeric_dist.mean():.1f}  |  Max: {int(numeric_dist.max())}")

    write_week_ahead(assignments, config, leave_by_day, prefills)
