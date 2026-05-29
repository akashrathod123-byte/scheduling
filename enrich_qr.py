"""Enrich Cleaned Up tab with customer info from visit and IP lookups."""
import csv
from copy import copy
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill

QR_FILE     = '/root/.claude/uploads/329da2eb-3c16-4332-b1c4-eff6fa478b4d/5700f49a-QR_Code_Data.xlsx'
IP_FILE     = '/root/.claude/uploads/329da2eb-3c16-4332-b1c4-eff6fa478b4d/9abe236f-ip.csv'
VISITS_FILE = '/root/.claude/uploads/329da2eb-3c16-4332-b1c4-eff6fa478b4d/a0e41266-visits.xlsx'
OUT_FILE    = '/home/user/scheduling/QR_Code_Data_enriched.xlsx'

def clean(v):
    if v is None: return None
    s = str(v).strip()
    if s == '' or s.upper() == 'NULL': return None
    return s

# ── Build visit_id → list[dict] from visits.xlsx ──────────────────────────────
visit_lookup = {}
wb_v = load_workbook(VISITS_FILE)
ws_v = wb_v['Sheet1']
v_headers = [c.value for c in ws_v[1]]
for row in ws_v.iter_rows(min_row=2, values_only=True):
    rec = dict(zip(v_headers, row))
    vid = clean(rec.get('visit_id'))
    cmf = clean(rec.get('cmf_id'))
    if not vid or not cmf:
        continue
    visit_lookup.setdefault(vid, []).append({
        'cmf_id': cmf,
        'ship_to_cmf_name': clean(rec.get('ship_to_cmf_name')),
        'city':     clean(rec.get('city')),
        'state':    clean(rec.get('state')),
        'zip':      clean(rec.get('zip')),
        'country':  clean(rec.get('country')),
        'listcode': clean(rec.get('listcode')),
        'role':     clean(rec.get('role')),
        'branch':   clean(rec.get('branch')),
        'mode':     clean(rec.get('mode')),
    })

# ── Build client_ip → list[dict] from ip.csv (NO header in file) ──────────────
ip_lookup = {}
ip_cols = ['client_ip','visit_id','visit_server_start_ts','visitor_id','contact_id',
           'cmf_id','ship_to_cmf_name','city','state','zip','country',
           'listcode','role','branch','mode']
with open(IP_FILE, encoding='utf-8-sig') as f:
    for row in csv.reader(f):
        rec = dict(zip(ip_cols, row))
        ip = clean(rec.get('client_ip'))
        cmf = clean(rec.get('cmf_id'))
        if not ip or not cmf:
            continue
        ip_lookup.setdefault(ip, []).append({
            'cmf_id': cmf,
            'ship_to_cmf_name': clean(rec.get('ship_to_cmf_name')),
            'city':     clean(rec.get('city')),
            'state':    clean(rec.get('state')),
            'zip':      clean(rec.get('zip')),
            'country':  clean(rec.get('country')),
            'listcode': clean(rec.get('listcode')),
            'role':     clean(rec.get('role')),
            'branch':   clean(rec.get('branch')),
            'mode':     clean(rec.get('mode')),
        })

print(f"Visits: {len(visit_lookup):,} visit_ids with CMF matches "
      f"({sum(len(v) for v in visit_lookup.values()):,} mappings)")
print(f"IPs:    {len(ip_lookup):,} IPs with CMF matches "
      f"({sum(len(v) for v in ip_lookup.values()):,} mappings)")

TOP_N = 10  # cap rendered CMFs to this many

def rank_and_cap(recs):
    """Dedupe by cmf_id but keep the FIRST occurrence; rank by frequency in source."""
    from collections import Counter
    freq = Counter(r['cmf_id'] for r in recs)
    seen = set(); deduped = []
    for r in recs:
        if r['cmf_id'] in seen: continue
        seen.add(r['cmf_id']); deduped.append(r)
    # rank by frequency desc, then keep first TOP_N
    deduped.sort(key=lambda r: -freq[r['cmf_id']])
    return deduped, len(deduped)

def joinlist(recs, key, sep=' | '):
    vals = [r.get(key) or '' for r in recs[:TOP_N]]
    if not any(vals): return None
    return sep.join(vals)

# ── Open original workbook and add columns to Cleaned Up ─────────────────────
wb = load_workbook(QR_FILE)
ws = wb['Cleaned Up']

# Find visit_id and client_ip columns
headers = [c.value for c in ws[1]]
vid_col = headers.index('visit_id') + 1
ip_col  = headers.index('client_ip') + 1

# Append new headers
new_headers = [
    'match_source',          # visit / ip / both / none
    'distinct_cmf_count',    # total distinct CMFs found (uncapped)
    'cmfs_shown',            # number shown below (capped at TOP_N)
    f'cmf_ids (top {TOP_N})',
    'ship_to_names',
    'cities',
    'states',
    'zips',
    'countries',
    'listcodes',
    'roles',
    'branches',
    'modes',
]
start_col = ws.max_column + 1
header_font = Font(bold=True)
header_fill = PatternFill('solid', fgColor='E8EEF3')
for i, h in enumerate(new_headers):
    cell = ws.cell(row=1, column=start_col + i, value=h)
    cell.font = header_font
    cell.fill = header_fill

# Fill rows
n_visit, n_ip, n_both, n_none = 0,0,0,0
for r in range(2, ws.max_row + 1):
    vid = clean(ws.cell(row=r, column=vid_col).value)
    ip  = clean(ws.cell(row=r, column=ip_col ).value)

    v_recs = visit_lookup.get(vid, []) if vid else []
    i_recs = ip_lookup.get(ip, [])      if ip  else []

    if v_recs and i_recs:    src = 'both';  n_both += 1
    elif v_recs:             src = 'visit'; n_visit+= 1
    elif i_recs:             src = 'ip';    n_ip   += 1
    else:                    src = 'none';  n_none += 1

    combined, total = rank_and_cap(v_recs + i_recs)
    shown = min(total, TOP_N)

    vals = [
        src,
        total,
        shown,
        joinlist(combined, 'cmf_id'),
        joinlist(combined, 'ship_to_cmf_name'),
        joinlist(combined, 'city'),
        joinlist(combined, 'state'),
        joinlist(combined, 'zip'),
        joinlist(combined, 'country'),
        joinlist(combined, 'listcode'),
        joinlist(combined, 'role'),
        joinlist(combined, 'branch'),
        joinlist(combined, 'mode'),
    ]
    for i, v in enumerate(vals):
        ws.cell(row=r, column=start_col + i, value=v)

# Set widths
widths = {0:14, 1:12, 2:12, 3:50, 4:50, 5:40, 6:18, 7:25, 8:25, 9:18, 10:30, 11:14, 12:18}
from openpyxl.utils import get_column_letter
for off, w in widths.items():
    ws.column_dimensions[get_column_letter(start_col + off)].width = w

wb.save(OUT_FILE)
print(f"\nSaved → {OUT_FILE}")
print(f"\nMatch sources across {ws.max_row - 1} rows:")
print(f"  both  {n_both:>4}")
print(f"  visit {n_visit:>4}")
print(f"  ip    {n_ip:>4}")
print(f"  none  {n_none:>4}")
