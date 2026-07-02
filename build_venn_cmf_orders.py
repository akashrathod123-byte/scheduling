"""Single 11x17 landscape PDF: CMF-level rules (R1 ∩ R3), sub-bubbles per listcode & threshold band."""
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch
import matplotlib as mpl

mpl.rcParams['font.family'] = 'DejaVu Sans'

# --- COLORS ---
R3_C   = '#a63a48'   # deep red
R3_BUB = '#8f2938'   # bubble fill
R1_C   = '#3b6e8a'   # steel blue
R1_BUB = '#2d5a72'
SWEET  = '#2d7a3b'
OVERLAP = '#7f2a94'
INK, INK2, MUTED = '#1a1a1a', '#4a4a4a', '#8a8a8a'

# --- DATA (orders metric) ---
UNIVERSE   = 17_028_786
R3_TOTAL   = 1_007_921
R1_TOTAL   = 4_288_615
BOTH_EST   = 60_000       # rough estimate for R1 ∩ R3 orders
ELIGIBLE   = UNIVERSE - R3_TOTAL - R1_TOTAL + BOTH_EST   # ~11.79M

MAX_ORDERS = 1_752_777     # 50+ band — biggest sub-bubble

def bubble_r(orders):
    return max(0.13, 1.40 * (orders / MAX_ORDERS) ** 0.5)

# --- FIGURE ---
fig = plt.figure(figsize=(17, 11), dpi=100)
fig.patch.set_facecolor('white')
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 17)
ax.set_ylim(0, 11)
ax.set_aspect('equal')
ax.axis('off')

# --- TITLE ---
ax.text(8.5, 10.5, 'CMF-Level Rules · Orders Blocked',
        ha='center', va='top', fontsize=22, fontweight='bold', color=INK)
ax.text(8.5, 9.85,
        'Rules 1 and 3 apply to shipping locations. Sub-bubbles inside each rule are individual '
        'listcodes (R3) and contact-count bands (R1), sized on a common orders scale.',
        ha='center', va='top', fontsize=11, color=INK2)
ax.text(8.5, 9.45, 'Universe: 17.0M contact-attributable orders',
        ha='center', va='top', fontsize=10, color=MUTED, style='italic')

# --- BIG VENN CIRCLES (soft fill so sub-bubbles pop) ---
R3_CENTER = (5.5, 4.8)
R1_CENTER = (11.5, 4.8)
BIG_R = 3.7

ax.add_patch(Circle(R3_CENTER, BIG_R, facecolor=R3_C, alpha=0.09,
                    edgecolor=R3_C, linewidth=2.5))
ax.add_patch(Circle(R1_CENTER, BIG_R, facecolor=R1_C, alpha=0.09,
                    edgecolor=R1_C, linewidth=2.5))

# --- R3 SUB-BUBBLES: listcodes ---
listcodes = [
    ('Distributor',       '97', 387_394, (5.0, 5.6)),
    ('Municipal',         '08', 222_199, (3.7, 4.0)),
    ('State Gov',         '07', 184_911, (5.7, 3.5)),
    ('University',        '09', 112_332, (6.7, 5.2)),
    ('Fed Gov (Dom.)',    '05',  58_169, (3.4, 5.5)),
    ('McMaster Internal', '15',  42_130, (6.6, 6.4)),
    ('Fed Gov (APO/FPO)', '06',     786, (3.9, 6.5)),
]

for name, code, orders, (x, y) in listcodes:
    r = bubble_r(orders)
    ax.add_patch(Circle((x, y), r, facecolor=R3_BUB, alpha=0.90,
                        edgecolor='white', linewidth=1.4))
    # Labels inside if bubble is big enough, otherwise pointer
    if r >= 0.32:
        ax.text(x, y + 0.10, name, ha='center', va='center', color='white',
                fontsize=8.5, fontweight='bold')
        ax.text(x, y - 0.14, f'{orders/1000:.0f}K orders',
                ha='center', va='center', color='white', fontsize=7)
    else:
        # small bubble — external label
        ax.text(x, y - r - 0.20, f'{name}\n{orders:,}',
                ha='center', va='top', color=INK, fontsize=6.8)

# --- R1 SUB-BUBBLES: threshold bands ---
bands = [
    ('50+',   1_752_777, (12.3, 4.8)),
    ('25–49',   678_000, (10.5, 7.3)),
    ('10–11',   510_570, (13.6, 6.9)),
    ('12–14',   510_187, (13.9, 4.2)),
    ('15–19',   509_758, (10.7, 3.0)),
    ('20–24',   327_323, (12.7, 2.6)),
]

for name, orders, (x, y) in bands:
    r = bubble_r(orders)
    ax.add_patch(Circle((x, y), r, facecolor=R1_BUB, alpha=0.90,
                        edgecolor='white', linewidth=1.4))
    if r >= 0.32:
        ax.text(x, y + 0.18, name + ' contacts', ha='center', va='center',
                color='white', fontsize=9, fontweight='bold')
        ax.text(x, y - 0.16, f'{orders/1000:.0f}K orders',
                ha='center', va='center', color='white', fontsize=7.5)

# --- OUTER RULE LABELS ---
# R3 (left panel)
ax.text(1.7, 8.4, 'Rule 3', color=R3_C, fontweight='bold', fontsize=17, ha='left')
ax.text(1.7, 8.02, 'Listcode', color=INK, fontsize=12, ha='left', fontweight='500')
ax.text(1.7, 7.62, 'Shipping locations with',    color=INK2, fontsize=9.5, ha='left')
ax.text(1.7, 7.40, 'list codes for government,', color=INK2, fontsize=9.5, ha='left')
ax.text(1.7, 7.18, 'college, distributor, or',    color=INK2, fontsize=9.5, ha='left')
ax.text(1.7, 6.96, 'internal.',                   color=INK2, fontsize=9.5, ha='left')
ax.text(1.7, 6.50, f'Blocks {R3_TOTAL/1e6:.2f}M orders',
        color=R3_C, fontweight='bold', fontsize=11, ha='left')
ax.text(1.7, 6.24, f'({R3_TOTAL/UNIVERSE*100:.1f}% of universe)',
        color=INK2, fontsize=9.5, ha='left')

# R1 (right panel)
ax.text(15.3, 8.4, 'Rule 1', color=R1_C, fontweight='bold', fontsize=17, ha='right')
ax.text(15.3, 8.02, 'Contact count', color=INK, fontsize=12, ha='right', fontweight='500')
ax.text(15.3, 7.62, 'Shipping locations with 10',   color=INK2, fontsize=9.5, ha='right')
ax.text(15.3, 7.40, 'or more active ordering',      color=INK2, fontsize=9.5, ha='right')
ax.text(15.3, 7.18, 'contacts.',                    color=INK2, fontsize=9.5, ha='right')
ax.text(15.3, 6.50, f'Blocks {R1_TOTAL/1e6:.2f}M orders',
        color=R1_C, fontweight='bold', fontsize=11, ha='right')
ax.text(15.3, 6.24, f'({R1_TOTAL/UNIVERSE*100:.1f}% of universe)',
        color=INK2, fontsize=9.5, ha='right')

# --- OVERLAP CALLOUT (in the lens) ---
lens_x = (R3_CENTER[0] + R1_CENTER[0]) / 2
ax.text(lens_x, 5.6, 'R1 ∩ R3', ha='center', va='center',
        color=OVERLAP, fontweight='bold', fontsize=10)
ax.text(lens_x, 5.25, '1,446', ha='center', va='center',
        color=OVERLAP, fontweight='bold', fontsize=16)
ax.text(lens_x, 4.95, 'CMFs fail both', ha='center', va='center',
        color=OVERLAP, fontsize=8.5)
ax.text(lens_x, 4.15, '(both a bad listcode', ha='center', va='center',
        color=MUTED, fontsize=7.5, style='italic')
ax.text(lens_x, 3.95, 'and 10+ contacts)', ha='center', va='center',
        color=MUTED, fontsize=7.5, style='italic')

# --- ELIGIBLE POOL LABEL (bottom, outside both circles) ---
ax.text(8.5, 1.05, 'Eligible pool',
        ha='center', va='center', fontsize=13, fontweight='bold', color=SWEET)
ax.text(8.5, 0.65, f'≈ {ELIGIBLE/1e6:.1f}M orders  ·  {ELIGIBLE/UNIVERSE*100:.0f}% of universe',
        ha='center', va='center', fontsize=11, color=INK)

# --- KEY INSIGHT CALLOUT ---
ax.text(8.5, 1.9,
        'The single 50+ contacts band blocks more orders than ALL R3 listcodes combined.',
        ha='center', va='center', fontsize=10.5, color=INK, style='italic',
        fontweight='500')

# --- FOOTER: sizing legend ---
ax.text(0.5, 0.4, 'Bubble size ∝ orders blocked   ·   Same scale across both rules',
        ha='left', va='center', fontsize=9, color=MUTED)

fig.savefig('/home/user/scheduling/venn_cmf_orders_11x17.pdf',
            bbox_inches='tight', pad_inches=0.25)
fig.savefig('/home/user/scheduling/venn_cmf_orders_11x17.png',
            dpi=200, bbox_inches='tight', pad_inches=0.25)
plt.close(fig)
print("Saved venn_cmf_orders_11x17.pdf and .png")
