"""Single 11x17 landscape: CMF-level rules with sub-bubbles that actually fill the space.

Metric: CMFs (shipping locations). Universe = ~555K active CMFs.
R3 sub-bubbles = individual listcodes.  R1 sub-bubbles = contact-count bands.
Per-rule bubble sizing (Distributor fills R3, 10-11 band fills R1) so both circles pack well.
"""
import math
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import matplotlib as mpl

mpl.rcParams['font.family'] = 'DejaVu Sans'

# --- COLORS ---
R3_C, R3_BUB = '#a63a48', '#8f2938'
R1_C, R1_BUB = '#3b6e8a', '#2d5a72'
SWEET, OVERLAP = '#2d7a3b', '#7f2a94'
INK, INK2, MUTED = '#1a1a1a', '#4a4a4a', '#8a8a8a'

# --- DATA (CMFs metric) ---
UNIVERSE  = 554_765
R3_TOTAL  = 50_000       # listcodes 05+06+07+08+09+15+97
R1_TOTAL  = 12_338
BOTH      = 1_446
ELIGIBLE  = UNIVERSE - R3_TOTAL - R1_TOTAL + BOTH   # ≈ 493,873

# --- LISTCODES for R3 (with CMFs) ---
listcodes = [
    # name, code, CMFs
    ('Distributor',       '97', 21_547),
    ('Municipal',         '08', 16_009),
    ('State Gov',         '07',  6_798),
    ('Fed Gov (Domestic)','05',  3_032),
    ('University',        '09',  2_423),
    ('Fed Gov (APO/FPO)', '06',    186),
    ('McMaster Internal', '15',      5),
]

# --- THRESHOLD BANDS for R1 (with CMFs) ---
bands = [
    ('10–11 contacts', 3_350),
    ('12–14 contacts', 2_864),
    ('15–19 contacts', 2_391),
    ('25–49 contacts', 1_761),
    ('20–24 contacts', 1_221),
    ('50+ contacts',      751),
]

# --- BUBBLE SIZING (per rule so each fills its container) ---
R3_MAX_SUB = 21_547   # Distributor
R1_MAX_SUB = 3_350    # 10-11 band

def r_r3(cmfs, biggest_r=1.85, floor=0.30):
    return max(floor, biggest_r * math.sqrt(cmfs / R3_MAX_SUB))

def r_r1(cmfs, biggest_r=1.55, floor=0.30):
    return max(floor, biggest_r * math.sqrt(cmfs / R1_MAX_SUB))

# --- FIGURE ---
# figsize chosen so the PDF prints inside 8x14 landscape paper (14 wide, 8 tall).
# Aspect matches the 17-unit-wide by 11-unit-tall content coord system.
fig = plt.figure(figsize=(12.36, 8.0), dpi=100)
fig.patch.set_facecolor('white')
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 17); ax.set_ylim(0, 11); ax.set_aspect('equal'); ax.axis('off')

# --- MASTHEAD ---
ax.text(8.5, 10.55, 'CMF-Level Rules  ·  Shipping Locations Blocked',
        ha='center', va='top', fontsize=24, fontweight='bold', color=INK)
ax.text(8.5, 9.95,
        'R3 (listcode) and R1 (contact count) both apply to shipping locations. '
        'Sub-bubbles inside each rule show the composition by listcode and by contact-count band.',
        ha='center', va='top', fontsize=11.5, color=INK2)
ax.text(8.5, 9.55, f'Universe: {UNIVERSE:,} active CMFs',
        ha='center', va='top', fontsize=10, color=MUTED, style='italic')

# --- BIG VENN CIRCLES (soft fill so sub-bubbles pop) ---
R3_CENTER = (5.0, 5.0); R1_CENTER = (12.0, 5.0)
BIG_R = 4.2
ax.add_patch(Circle(R3_CENTER, BIG_R, facecolor=R3_C, alpha=0.08,
                    edgecolor=R3_C, linewidth=2.5))
ax.add_patch(Circle(R1_CENTER, BIG_R, facecolor=R1_C, alpha=0.08,
                    edgecolor=R1_C, linewidth=2.5))

# --- RULE LABELS at the outer corners ---
# Rule 3 (top-left)
ax.text(0.5, 8.9, 'Rule 3', color=R3_C, fontweight='bold', fontsize=19, ha='left')
ax.text(0.5, 8.48, 'Listcode', color=INK, fontsize=13, ha='left')
ax.text(0.5, 8.13, 'Shipping locations with',    color=INK2, fontsize=10, ha='left')
ax.text(0.5, 7.92, 'list codes for government,', color=INK2, fontsize=10, ha='left')
ax.text(0.5, 7.71, 'college, distributor,',      color=INK2, fontsize=10, ha='left')
ax.text(0.5, 7.50, 'or internal.',               color=INK2, fontsize=10, ha='left')
ax.text(0.5, 7.05, f'Blocks {R3_TOTAL:,} CMFs',
        color=R3_C, fontweight='bold', fontsize=12, ha='left')
ax.text(0.5, 6.80, f'{R3_TOTAL/UNIVERSE*100:.1f}% of universe',
        color=INK2, fontsize=10, ha='left')

# Rule 1 (top-right)
ax.text(16.5, 8.9, 'Rule 1', color=R1_C, fontweight='bold', fontsize=19, ha='right')
ax.text(16.5, 8.48, 'Contact count', color=INK, fontsize=13, ha='right')
ax.text(16.5, 8.13, 'Shipping locations with',      color=INK2, fontsize=10, ha='right')
ax.text(16.5, 7.92, '10 or more active ordering',   color=INK2, fontsize=10, ha='right')
ax.text(16.5, 7.71, 'contacts.',                    color=INK2, fontsize=10, ha='right')
ax.text(16.5, 7.05, f'Blocks {R1_TOTAL:,} CMFs',
        color=R1_C, fontweight='bold', fontsize=12, ha='right')
ax.text(16.5, 6.80, f'{R1_TOTAL/UNIVERSE*100:.1f}% of universe',
        color=INK2, fontsize=10, ha='right')

# --- R3 SUB-BUBBLES (arranged to fill R3 circle) ---
# Manually positioned for a compact pack; largest at center-ish
listcode_positions = {
    'Distributor':       (4.2, 4.7),   # biggest, center-left
    'Municipal':         (6.6, 5.6),   # upper-right of R3
    'State Gov':         (4.0, 7.4),   # top-left area
    'Fed Gov (Domestic)':(6.4, 3.2),   # lower-right
    'University':        (2.3, 5.9),   # far left
    'Fed Gov (APO/FPO)': (2.8, 3.8),   # lower-left small
    'McMaster Internal': (3.4, 2.6),   # bottom-left tiny
}

for name, code, cmfs in listcodes:
    x, y = listcode_positions[name]
    r = r_r3(cmfs)
    ax.add_patch(Circle((x, y), r, facecolor=R3_BUB, alpha=0.92,
                        edgecolor='white', linewidth=1.6))
    if r >= 0.85:
        # big bubble — big number front and center
        ax.text(x, y + 0.35, name, ha='center', va='center',
                color='white', fontsize=10.5, fontweight='bold', alpha=0.92)
        ax.text(x, y - 0.10, f'{cmfs:,}', ha='center', va='center',
                color='white', fontsize=18, fontweight='bold')
    elif r >= 0.55:
        ax.text(x, y + 0.25, name, ha='center', va='center',
                color='white', fontsize=9.5, fontweight='bold', alpha=0.92)
        ax.text(x, y - 0.08, f'{cmfs:,}', ha='center', va='center',
                color='white', fontsize=14, fontweight='bold')
    elif r >= 0.40:
        ax.text(x, y + 0.14, name.split()[0][:9], ha='center', va='center',
                color='white', fontsize=8, fontweight='bold', alpha=0.92)
        ax.text(x, y - 0.10, f'{cmfs:,}', ha='center', va='center',
                color='white', fontsize=11, fontweight='bold')
    else:
        # too small — label outside with leader
        ax.text(x, y - r - 0.30, f'{name}\n{cmfs:,}',
                ha='center', va='top', color=INK, fontsize=8)

# --- R1 SUB-BUBBLES ---
band_positions = {
    '10–11 contacts':  (11.6, 5.1),  # biggest, near center
    '12–14 contacts':  (13.9, 6.4),  # upper-right
    '15–19 contacts':  (9.9,  6.8),  # upper-left
    '25–49 contacts':  (14.0, 3.8),  # lower-right
    '20–24 contacts':  (10.4, 3.4),  # lower-left
    '50+ contacts':    (14.6, 5.6),  # small far right (highlighted)
}

for name, cmfs in bands:
    x, y = band_positions[name]
    r = r_r1(cmfs)
    ax.add_patch(Circle((x, y), r, facecolor=R1_BUB, alpha=0.92,
                        edgecolor='white', linewidth=1.6))
    if r >= 0.85:
        ax.text(x, y + 0.35, name, ha='center', va='center',
                color='white', fontsize=10.5, fontweight='bold', alpha=0.92)
        ax.text(x, y - 0.10, f'{cmfs:,}', ha='center', va='center',
                color='white', fontsize=18, fontweight='bold')
    elif r >= 0.60:
        ax.text(x, y + 0.24, name, ha='center', va='center',
                color='white', fontsize=9, fontweight='bold', alpha=0.92)
        ax.text(x, y - 0.10, f'{cmfs:,}', ha='center', va='center',
                color='white', fontsize=14, fontweight='bold')
    else:
        ax.text(x, y + 0.16, name.split()[0], ha='center', va='center',
                color='white', fontsize=8, fontweight='bold', alpha=0.92)
        ax.text(x, y - 0.10, f'{cmfs:,}', ha='center', va='center',
                color='white', fontsize=11, fontweight='bold')

# --- OVERLAP CALLOUT (in the lens) ---
lens_x = (R3_CENTER[0] + R1_CENTER[0]) / 2
ax.text(lens_x, 6.0, 'R1 ∩ R3', ha='center', va='center',
        color=OVERLAP, fontweight='bold', fontsize=11)
ax.text(lens_x, 5.55, f'{BOTH:,}', ha='center', va='center',
        color=OVERLAP, fontweight='bold', fontsize=22)
ax.text(lens_x, 5.15, 'CMFs fail both', ha='center', va='center',
        color=OVERLAP, fontsize=10)

# --- ELIGIBLE POOL FOOTER ---
ax.text(8.5, 0.95, 'Eligible pool',
        ha='center', va='center', fontsize=14, fontweight='bold', color=SWEET)
ax.text(8.5, 0.55, f'≈ {ELIGIBLE/1000:.0f}K CMFs   ·   {ELIGIBLE/UNIVERSE*100:.0f}% of universe',
        ha='center', va='center', fontsize=12, color=INK)

# --- LEGEND NOTE ---
ax.text(0.5, 0.30,
        'Bubble size ∝ CMFs blocked, scaled per rule so each circle is filled.',
        ha='left', va='center', fontsize=9, color=MUTED, style='italic')

fig.savefig('/home/user/scheduling/venn_cmf_11x17.pdf')          # exact 12.36 x 8 in
fig.savefig('/home/user/scheduling/venn_cmf_11x17.png', dpi=200)
plt.close(fig)
print("Saved venn_cmf_11x17.pdf and .png")
