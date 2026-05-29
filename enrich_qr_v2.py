"""Enrich Cleaned Up tab — drops CC noise when a real company is also matched,
then merges interaction summaries."""
import csv, re
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

QR_FILE     = '/root/.claude/uploads/329da2eb-3c16-4332-b1c4-eff6fa478b4d/5700f49a-QR_Code_Data.xlsx'
IP_FILE     = '/root/.claude/uploads/329da2eb-3c16-4332-b1c4-eff6fa478b4d/9abe236f-ip.csv'
VISITS_FILE = '/root/.claude/uploads/329da2eb-3c16-4332-b1c4-eff6fa478b4d/a0e41266-visits.xlsx'
SUMS_FILE   = '/root/.claude/uploads/329da2eb-3c16-4332-b1c4-eff6fa478b4d/f0fb8535-Interaction_Summaries.xlsx'
OUT_FILE    = '/home/user/scheduling/QR_Code_Data_enriched.xlsx'

TOP_N = 10
CC_RE = re.compile(r'credit\s*card', re.I)

def clean(v):
    if v is None: return None
    s = str(v).strip()
    return s if s and s.upper() != 'NULL' else None

def is_cc(rec):
    name = (rec.get('ship_to_cmf_name') or '')
    return bool(CC_RE.search(name))

# ── visit_id → list[dict] ─────────────────────────────────────────────────────
visit_lookup = {}
ws_v = load_workbook(VISITS_FILE)['Sheet1']
v_headers = [c.value for c in ws_v[1]]
for row in ws_v.iter_rows(min_row=2, values_only=True):
    rec = dict(zip(v_headers, row))
    vid = clean(rec.get('visit_id'))
    cmf = clean(rec.get('cmf_id'))
    if not vid or not cmf: continue
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

# ── client_ip → list[dict] (ip.csv has no header) ─────────────────────────────
ip_lookup = {}
ip_cols = ['client_ip','visit_id','visit_server_start_ts','visitor_id','contact_id',
           'cmf_id','ship_to_cmf_name','city','state','zip','country',
           'listcode','role','branch','mode']
with open(IP_FILE, encoding='utf-8-sig') as f:
    for row in csv.reader(f):
        rec = dict(zip(ip_cols, row))
        ip = clean(rec.get('client_ip')); cmf = clean(rec.get('cmf_id'))
        if not ip or not cmf: continue
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

# ── visit_id → summary ────────────────────────────────────────────────────────
summary = {}
ws_s = load_workbook(SUMS_FILE)['Summaries']
s_headers = [c.value for c in ws_s[1]]
for row in ws_s.iter_rows(min_row=2, values_only=True):
    rec = dict(zip(s_headers, row))
    vid = clean(rec.get('visit_id'))
    if vid: summary[vid] = rec

print(f"visits w/ CMF: {len(visit_lookup):,}")
print(f"IPs w/ CMF:    {len(ip_lookup):,}")
print(f"summaries:     {len(summary):,}")

def filter_cc_noise(recs):
    """Drop CC entries iff there's at least one non-CC entry; else keep all."""
    non_cc = [r for r in recs if not is_cc(r)]
    return non_cc if non_cc else recs

def rank_and_cap(recs):
    from collections import Counter
    freq = Counter(r['cmf_id'] for r in recs)
    seen = set(); deduped = []
    for r in recs:
        if r['cmf_id'] in seen: continue
        seen.add(r['cmf_id']); deduped.append(r)
    deduped.sort(key=lambda r: -freq[r['cmf_id']])
    return deduped

def joinlist(recs, key, sep=' | '):
    vals = [r.get(key) or '' for r in recs[:TOP_N]]
    return sep.join(vals) if any(vals) else None

# ── Build enriched workbook ───────────────────────────────────────────────────
wb = load_workbook(QR_FILE)
ws = wb['Cleaned Up']
headers = [c.value for c in ws[1]]
vid_col = headers.index('visit_id') + 1
ip_col  = headers.index('client_ip') + 1
start_col = ws.max_column + 1

new_headers = [
    'match_source','distinct_cmf_count','cmfs_shown',
    f'cmf_ids (top {TOP_N}, CC-filtered)',
    'ship_to_names','cities','states','zips','countries',
    'listcodes','roles','branches','modes',
    'cc_filtered',                     # 'yes' if CC noise was dropped
    'customer_info','timeline','narrative','frictions',
]
hdr_font = Font(bold=True)
hdr_fill = PatternFill('solid', fgColor='E8EEF3')
for i, h in enumerate(new_headers):
    cell = ws.cell(row=1, column=start_col + i, value=h)
    cell.font = hdr_font; cell.fill = hdr_fill

wrap = Alignment(wrap_text=True, vertical='top')
n_visit=n_ip=n_both=n_none=n_cc_dropped=0
for r in range(2, ws.max_row + 1):
    vid = clean(ws.cell(row=r, column=vid_col).value)
    ip  = clean(ws.cell(row=r, column=ip_col ).value)
    v_recs = visit_lookup.get(vid, []) if vid else []
    i_recs = ip_lookup.get(ip, [])      if ip  else []

    if v_recs and i_recs:    src = 'both';  n_both += 1
    elif v_recs:             src = 'visit'; n_visit+= 1
    elif i_recs:             src = 'ip';    n_ip   += 1
    else:                    src = 'none';  n_none += 1

    raw_combined = v_recs + i_recs
    pre_count = len({r['cmf_id'] for r in raw_combined})
    filtered = filter_cc_noise(raw_combined)
    post_count = len({r['cmf_id'] for r in filtered})
    cc_filtered = 'yes' if post_count < pre_count else ''
    if cc_filtered: n_cc_dropped += 1

    combined = rank_and_cap(filtered)
    total = len(combined)
    shown = min(total, TOP_N)

    s = summary.get(vid) if vid else None
    s_get = (lambda k: s.get(k) if s else None)

    vals = [
        src, total, shown,
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
        cc_filtered,
        s_get('customer_info'),
        s_get('timeline'),
        s_get('narrative'),
        s_get('frictions'),
    ]
    for i, v in enumerate(vals):
        cell = ws.cell(row=r, column=start_col + i, value=v)
        if i >= 13:  # text-heavy summary cols
            cell.alignment = wrap

# widths
w_map = [14,12,12,50,50,40,18,25,25,18,30,14,18,14,40,80,80,80]
for off, w in enumerate(w_map):
    ws.column_dimensions[get_column_letter(start_col + off)].width = w

wb.save(OUT_FILE)
print(f"\nSaved → {OUT_FILE}")
print(f"Rows: {ws.max_row - 1}")
print(f"  both  {n_both}   ip {n_ip}   visit {n_visit}   none {n_none}")
print(f"  CC-noise filtered on {n_cc_dropped} rows")
