"""Append 3 new May 30 visits to Cleaned Up tab and refresh weekly chart + stats."""
from openpyxl import load_workbook
from datetime import datetime
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

XLSX = '/home/user/scheduling/QR_Code_Data_enriched.xlsx'

NEW_ROWS = [
    # (yyyymm, ts, visit_id, browse_id, platform, ip, os, browser_desc, friendly_url, original_href, first_success, engagement_count, save_cad, share_product, has_info, add_to_order_count, has_pre_order)
    (202605, datetime(2026, 5, 30, 10, 30, 51), 'b053a4e442e144078effae1b6213a83a',
     '116644345991', 'mobile_website', '207.212.6.42', 'ios', 'safari 26.5 on apple iphone (ios 18.7)',
     '91578a863', 'https://www.mcmaster.com/91578a863/?mode=qr&codeid=4', None, 1, 0, 0, 0, 0, 0),
    (202605, datetime(2026, 5, 30, 10, 31, 3), '105e08cf961a422b94555b50e147c208',
     '123274315379', 'mobile_website', '107.115.224.5', 'ios', 'safari 26.5 on apple iphone (ios 18.7)',
     '91578a863', 'https://www.mcmaster.com/91578a863/?mode=qr&codeid=4', None, 1, 0, 0, 0, 0, 0),
    (202605, datetime(2026, 5, 30, 7, 5, 53), '70544a04d68a42aa92142f53dbbbff38',
     '158083953820', 'mobile_website', '50.151.209.1', 'android', 'chrome mobile 148.0.0.0 on k (android 10)',
     '92865a133', 'https://www.mcmaster.com/92865a133/?mode=qr&codeid=4', None, 1, 0, 0, 0, 0, 0),
]

wb = load_workbook(XLSX)
ws = wb['Cleaned Up']
start_row = ws.max_row + 1
hdr = [c.value for c in ws[1]]

# Append rows; leave enrichment cols (17+) blank since no triangulation match
for i, r in enumerate(NEW_ROWS):
    for j, v in enumerate(r):
        ws.cell(row=start_row + i, column=j + 1, value=v)
    # match_source = 'none' for new rows
    ws.cell(row=start_row + i, column=18, value='none')
    ws.cell(row=start_row + i, column=19, value=0)
    ws.cell(row=start_row + i, column=20, value=0)

wb.save(XLSX)
print(f"Appended {len(NEW_ROWS)} rows. New Cleaned Up row count: {ws.max_row - 1}")

# Recompute stats
ts_col   = hdr.index('search_start_user_action_server_ts')
part_col = hdr.index('friendly_url_txt')
eng_col  = hdr.index('user_action_engagement_count')
src_col  = hdr.index('match_source')
plat_col = hdr.index('platform')
os_col   = hdr.index('operating_system')
brw_col  = hdr.index('browser_description')

rows = list(ws.iter_rows(min_row=2, values_only=True))
total = len(rows)
print(f"\n=== UPDATED STATS ===")
print(f"Total scans: {total}")

# Date range
dates = sorted(r[ts_col] for r in rows if r[ts_col])
print(f"Date range: {dates[0]} → {dates[-1]}")

# Match rate
matched = sum(1 for r in rows if r[src_col] and r[src_col] != 'none')
print(f"Matched to known customer: {matched}/{total} ({matched/total:.0%})")

# Visit length table
buckets = Counter()
for r in rows:
    e = r[eng_col] or 0
    if e <= 1:    buckets['single'] += 1
    elif e <= 5:  buckets['2-5']    += 1
    else:         buckets['6+']     += 1
print(f"Visit length: single={buckets['single']} ({buckets['single']/total:.0%}), "
      f"2-5={buckets['2-5']} ({buckets['2-5']/total:.0%}), "
      f"6+={buckets['6+']} ({buckets['6+']/total:.0%})")

# Top parts
parts = Counter()
for r in rows:
    p = r[part_col]
    if p:
        parts[p.strip().upper()] += 1
print(f"\nDistinct parts: {len(parts)}")
print(f"Parts with 1 scan only: {sum(1 for c in parts.values() if c == 1)}")
print(f"Parts with 2+ scans: {sum(1 for c in parts.values() if c >= 2)}")
print(f"\nTop 12 parts:")
for p, c in parts.most_common(15):
    print(f"  {p}: {c}")

# Device/browser breakdown
mobile = sum(1 for r in rows if r[plat_col] and r[plat_col] != 'mcmaster_com')
mac_pc = sum(1 for r in rows if r[plat_col] == 'mcmaster_com')
ios = sum(1 for r in rows if r[os_col] == 'ios')
android = sum(1 for r in rows if r[os_col] == 'android')
print(f"\nMobile: {mobile} ({mobile/total:.0%}); Desktop: {mac_pc} ({mac_pc/total:.0%})")
print(f"iOS: {ios}; Android: {android}")
print(f"Of mobile: iOS={ios/mobile:.0%}, Android={android/mobile:.0%}")

# Weekly chart (week ending Sun)
weekly = Counter()
from datetime import timedelta
for r in rows:
    ts = r[ts_col]
    if not ts: continue
    # week start = Monday
    monday = ts.date() - timedelta(days=ts.weekday())
    weekly[monday] += 1

weeks = sorted(weekly.items())
print(f"\nWeekly scans ({len(weeks)} weeks):")
for d, c in weeks:
    print(f"  week of {d}: {c}")

# Generate chart
fig, ax = plt.subplots(figsize=(11, 4.5))
xs = [d for d, _ in weeks]
ys = [c for _, c in weeks]
ax.bar(xs, ys, width=5.5, color='#1f4e79', edgecolor='white')
ax.set_xlabel('Week starting (Monday)', fontsize=10)
ax.set_ylabel('QR scans', fontsize=10)
ax.set_title('Weekly QR scans — Prepack items', fontsize=12, fontweight='bold', loc='left')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
for x, y in zip(xs, ys):
    ax.text(x, y + 0.4, str(y), ha='center', va='bottom', fontsize=9)
import matplotlib.dates as mdates
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
fig.autofmt_xdate()
plt.tight_layout()
plt.savefig('/home/user/scheduling/qr_weekly.png', dpi=140, bbox_inches='tight')
print("\nSaved chart → qr_weekly.png")
