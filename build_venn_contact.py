"""Single 11x17 landscape: 3-circle Contact Venn (R2 ∩ R4 ∩ R1).

Metric: contacts (ordering contacts).  Universe = 1.39M.
Three circles — R2 (ship-to orders, plum) top-left, R4 (multi-billto, gold) top-right,
R1 (contact count, steel-blue) bottom. R1 is CMF-level but reframed as "contact is at a
shipping location with 10+ contacts" so the whole Venn stays in the contact metric.
Sub-bubbles inside each circle show composition.
"""
import math
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import matplotlib as mpl

mpl.rcParams['font.family'] = 'DejaVu Sans'

# --- COLORS ---
R2_C, R2_BUB = '#6f4859', '#523240'   # dusty plum
R4_C, R4_BUB = '#c78321', '#9e6318'   # warm gold
R1_C, R1_BUB = '#3b6e8a', '#2d5a72'   # steel blue
SWEET = '#2d7a3b'
INK, INK2, MUTED = '#1a1a1a', '#4a4a4a', '#8a8a8a'

# --- DATA (contacts metric) ---
UNIVERSE  = 1_386_228
R2_TOTAL  = 611_259
R4_TOTAL  = 43_487
R1_TOTAL  = 248_827
# Rough eligible under independence:  ~1.39M × (1-p_R2)(1-p_R4)(1-p_R1)
ELIGIBLE  = 623_000

# --- R2 SUB-BUCKETS (order-count patterns) ---
r2_buckets = [
    ('1 order in year',                 506_925),
    ('2 orders in year',                 92_000),
    ('3+ orders, scattered ship-tos',    12_334),
]

# --- R4 SUB-BUCKETS (billto count) ---
r4_buckets = [
    ('2 billtos',    25_000),
    ('3 billtos',     8_000),
    ('4 billtos',     4_000),
    ('5 billtos',     2_500),
    ('6–9 billtos',   2_500),
    ('10+ billtos',   1_487),
]

# --- R1 SUB-BUCKETS (contact-count band at the CMF) ---
# Contact-level estimates: contacts at CMFs in each band (~248K total)
r1_buckets = [
    ('25–49 contacts', 65_000),
    ('50+ contacts',    43_000),
    ('15–19 contacts',  41_000),
    ('12–14 contacts',  37_000),
    ('10–11 contacts',  35_000),
    ('20–24 contacts',  27_000),
]

# --- BUBBLE SIZING (per rule, biggest = ~40% of big-circle radius) ---
def make_size_fn(max_val, biggest_r=1.35, floor=0.30):
    return lambda x: max(floor, biggest_r * math.sqrt(x / max_val))

r_r2 = make_size_fn(506_925, biggest_r=1.55)
r_r4 = make_size_fn( 25_000, biggest_r=1.40)
r_r1 = make_size_fn( 65_000, biggest_r=1.25)

# --- FIGURE ---
# figsize chosen so the PDF prints inside 8x14 landscape paper (14 wide, 8 tall).
fig = plt.figure(figsize=(12.36, 8.0), dpi=100)
fig.patch.set_facecolor('white')
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 17); ax.set_ylim(0, 11); ax.set_aspect('equal'); ax.axis('off')

# --- MASTHEAD ---
ax.text(8.5, 10.55, 'Contact-Level Rules  ·  Contacts Blocked',
        ha='center', va='top', fontsize=23, fontweight='bold', color=INK)
ax.text(8.5, 9.95,
        'R2 (ship-to orders), R4 (multi-billto), and R1 (contact at a high-headcount CMF) '
        'all evaluated per contact. Sub-bubbles inside each rule show its composition.',
        ha='center', va='top', fontsize=11, color=INK2)
ax.text(8.5, 9.55, f'Universe: {UNIVERSE:,} ordering contacts',
        ha='center', va='top', fontsize=10, color=MUTED, style='italic')

# --- 3 BIG CIRCLES (inverted triangle: R2 top-left, R4 top-right, R1 bottom) ---
R2_CENTER = (5.5, 6.4)
R4_CENTER = (11.5, 6.4)
R1_CENTER = (8.5, 3.3)
BIG_R = 3.5

ax.add_patch(Circle(R2_CENTER, BIG_R, facecolor=R2_C, alpha=0.11,
                    edgecolor=R2_C, linewidth=2.3))
ax.add_patch(Circle(R4_CENTER, BIG_R, facecolor=R4_C, alpha=0.11,
                    edgecolor=R4_C, linewidth=2.3))
ax.add_patch(Circle(R1_CENTER, BIG_R, facecolor=R1_C, alpha=0.11,
                    edgecolor=R1_C, linewidth=2.3))

# --- RULE LABELS ---
# R2 label — outer upper-left
ax.text(0.3, 8.4, 'Rule 2', color=R2_C, fontweight='bold', fontsize=17, ha='left')
ax.text(0.3, 8.0, 'Ship-to orders', color=INK, fontsize=11.5, ha='left')
ax.text(0.3, 7.7, 'Contacts who have placed',  color=INK2, fontsize=9.5, ha='left')
ax.text(0.3, 7.5, 'fewer than 3 orders at the', color=INK2, fontsize=9.5, ha='left')
ax.text(0.3, 7.3, 'same ship-to location.',     color=INK2, fontsize=9.5, ha='left')
ax.text(0.3, 6.95, f'{R2_TOTAL:,} contacts',
        color=R2_C, fontweight='bold', fontsize=11, ha='left')
ax.text(0.3, 6.72, f'{R2_TOTAL/UNIVERSE*100:.0f}% of universe',
        color=INK2, fontsize=9.5, ha='left')

# R4 label — outer upper-right
ax.text(16.7, 8.4, 'Rule 4', color=R4_C, fontweight='bold', fontsize=17, ha='right')
ax.text(16.7, 8.0, 'Multi-billto', color=INK, fontsize=11.5, ha='right')
ax.text(16.7, 7.7, 'Contacts who order across',   color=INK2, fontsize=9.5, ha='right')
ax.text(16.7, 7.5, 'more than one non-individual', color=INK2, fontsize=9.5, ha='right')
ax.text(16.7, 7.3, 'billing location.',            color=INK2, fontsize=9.5, ha='right')
ax.text(16.7, 6.95, f'{R4_TOTAL:,} contacts',
        color=R4_C, fontweight='bold', fontsize=11, ha='right')
ax.text(16.7, 6.72, f'{R4_TOTAL/UNIVERSE*100:.0f}% of universe',
        color=INK2, fontsize=9.5, ha='right')

# R1 label — outer lower-left (below R2 label area, or under R1 circle)
# R1 circle bottom is at y ~ -0.2 (off canvas); position label to the left of R1
ax.text(0.3, 2.5, 'Rule 1', color=R1_C, fontweight='bold', fontsize=17, ha='left')
ax.text(0.3, 2.1, 'Contact count', color=INK, fontsize=11.5, ha='left')
ax.text(0.3, 1.8, 'Contacts at a shipping',    color=INK2, fontsize=9.5, ha='left')
ax.text(0.3, 1.6, 'location with 10 or more',  color=INK2, fontsize=9.5, ha='left')
ax.text(0.3, 1.4, 'active ordering contacts.', color=INK2, fontsize=9.5, ha='left')
ax.text(0.3, 1.05, f'{R1_TOTAL:,} contacts',
        color=R1_C, fontweight='bold', fontsize=11, ha='left')
ax.text(0.3, 0.82, f'{R1_TOTAL/UNIVERSE*100:.0f}% of universe',
        color=INK2, fontsize=9.5, ha='left')

# --- Sub-bubble drawing helper ---
def draw_bubble(x, y, r, name, val, color):
    ax.add_patch(Circle((x, y), r, facecolor=color, alpha=0.92,
                        edgecolor='white', linewidth=1.4))
    if r >= 0.85:
        ax.text(x, y + 0.30, name, ha='center', va='center',
                color='white', fontsize=9.5, fontweight='bold', alpha=0.92)
        ax.text(x, y - 0.10, f'{val:,}', ha='center', va='center',
                color='white', fontsize=15, fontweight='bold')
    elif r >= 0.55:
        ax.text(x, y + 0.20, name, ha='center', va='center',
                color='white', fontsize=8.5, fontweight='bold', alpha=0.92)
        ax.text(x, y - 0.10, f'{val:,}', ha='center', va='center',
                color='white', fontsize=12, fontweight='bold')
    else:
        ax.text(x, y + 0.14, name.split()[0], ha='center', va='center',
                color='white', fontsize=7.5, fontweight='bold', alpha=0.92)
        ax.text(x, y - 0.09, f'{val:,}', ha='center', va='center',
                color='white', fontsize=9, fontweight='bold')

# --- R2 SUB-BUBBLES (upper-left crescent of R2) ---
r2_positions = {
    '1 order in year':                (4.3, 6.7),
    '2 orders in year':               (3.4, 5.0),
    '3+ orders, scattered ship-tos':  (6.7, 7.9),
}
for name, val in r2_buckets:
    x, y = r2_positions[name]
    draw_bubble(x, y, r_r2(val), name, val, R2_BUB)

# --- R4 SUB-BUBBLES (upper-right crescent of R4) ---
r4_positions = {
    '2 billtos':    (12.7, 6.7),
    '3 billtos':    (13.6, 5.0),
    '4 billtos':    (10.5, 7.9),
    '5 billtos':    (13.9, 7.7),
    '6–9 billtos':  (12.3, 8.2),
    '10+ billtos':  (14.2, 6.0),
}
for name, val in r4_buckets:
    x, y = r4_positions[name]
    draw_bubble(x, y, r_r4(val), name, val, R4_BUB)

# --- R1 SUB-BUBBLES (bottom crescent of R1) ---
r1_positions = {
    '25–49 contacts': (8.5, 2.4),
    '50+ contacts':   (5.9, 3.0),
    '15–19 contacts': (11.1, 3.0),
    '12–14 contacts': (7.0, 0.9),
    '10–11 contacts': (10.0, 0.9),
    '20–24 contacts': (8.5, 4.4),
}
for name, val in r1_buckets:
    x, y = r1_positions[name]
    draw_bubble(x, y, r_r1(val), name, val, R1_BUB)

# --- OVERLAP CALLOUTS (contacts failing multiple rules, est. under independence) ---
OVERLAP_C = '#7f2a94'

def overlap_tag(x, y, label, val):
    ax.text(x, y + 0.15, label, ha='center', va='center',
            color=OVERLAP_C, fontweight='bold', fontsize=9, alpha=0.95)
    ax.text(x, y - 0.10, val, ha='center', va='center',
            color=OVERLAP_C, fontweight='bold', fontsize=13)

# R1 ∩ R2 only (left side between R1 and R2, outside R4)
overlap_tag(6.0, 5.4, 'R1 ∩ R2', '≈107K')
# R2 ∩ R4 only (top between R2 and R4, above R1)
overlap_tag(8.5, 7.5, 'R2 ∩ R4', '≈16K')
# R1 ∩ R4 only (right side between R1 and R4, outside R2)
overlap_tag(11.0, 5.4, 'R1 ∩ R4', '≈4K')
# All three (center of triangle)
overlap_tag(8.5, 5.5, 'All 3', '≈3K')

# --- ELIGIBLE POOL — bottom-right callout ---
ax.text(16.7, 1.4, 'Passes all three rules',
        ha='right', va='center', fontsize=12, fontweight='bold', color=SWEET)
ax.text(16.7, 1.08, f'≈ {ELIGIBLE/1000:.0f}K contacts',
        ha='right', va='center', fontsize=11, color=INK)
ax.text(16.7, 0.85, f'({ELIGIBLE/UNIVERSE*100:.0f}% of universe · R3 not shown)',
        ha='right', va='center', fontsize=9, color=MUTED, style='italic')

# --- LEGEND NOTE ---
ax.text(0.3, 0.35,
        'Sub-bubbles = total contacts caught by each rule (may fall in more than one region). '
        'Overlaps estimated under independence.',
        ha='left', va='center', fontsize=8.5, color=MUTED, style='italic')

fig.savefig('/home/user/scheduling/venn_contact_11x17.pdf')          # exact 12.36 x 8 in
fig.savefig('/home/user/scheduling/venn_contact_11x17.png', dpi=200)
plt.close(fig)
print("Saved venn_contact_11x17.pdf and .png")
