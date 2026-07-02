"""Single 11x17 landscape: Contact-level rules (R2 ∩ R4) with sub-bubbles.

Metric: contacts (ordering contacts).  Universe = 1.39M contacts.
R2 sub-bubbles = order-count buckets.  R4 sub-bubbles = billto-count buckets.
Per-rule bubble sizing so each container is filled instead of half-empty.
"""
import math
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import matplotlib as mpl

mpl.rcParams['font.family'] = 'DejaVu Sans'

# --- COLORS (match the previous 4-rule palette) ---
R2_C, R2_BUB = '#6f4859', '#523240'   # dusty plum
R4_C, R4_BUB = '#c78321', '#9e6318'   # warm gold
SWEET, OVERLAP = '#2d7a3b', '#7f2a94'
INK, INK2, MUTED = '#1a1a1a', '#4a4a4a', '#8a8a8a'

# --- DATA (contacts metric) ---
UNIVERSE  = 1_386_228
R2_TOTAL  = 611_259
R4_TOTAL  = 43_487
BOTH_EST  = 19_000
ELIGIBLE  = UNIVERSE - R2_TOTAL - R4_TOTAL + BOTH_EST   # ≈ 750,482

# --- R2 SUB-BUCKETS (order-count) ---
r2_buckets = [
    ('1 order in year',   506_925),
    ('2 orders in year',  104_334),   # = R2 total - 1-order, to sum to 611K
]

# --- R4 SUB-BUCKETS (billto-count) ---
r4_buckets = [
    ('2 billtos',      30_000),
    ('3–5 billtos',    10_000),
    ('6+ billtos',      3_487),
]

# --- BUBBLE SIZING (per rule) ---
R2_MAX = 506_925    # 1-order bucket
R4_MAX = 30_000     # 2-billtos bucket

def r_r2(contacts, biggest_r=2.55, floor=0.40):
    return max(floor, biggest_r * math.sqrt(contacts / R2_MAX))

def r_r4(contacts, biggest_r=1.90, floor=0.35):
    return max(floor, biggest_r * math.sqrt(contacts / R4_MAX))

# --- FIGURE ---
fig = plt.figure(figsize=(17, 11), dpi=100)
fig.patch.set_facecolor('white')
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 17); ax.set_ylim(0, 11); ax.set_aspect('equal'); ax.axis('off')

# --- MASTHEAD ---
ax.text(8.5, 10.55, 'Contact-Level Rules  ·  Contacts Blocked',
        ha='center', va='top', fontsize=24, fontweight='bold', color=INK)
ax.text(8.5, 9.95,
        'R2 (ship-to orders) and R4 (multi-billto) both apply to individual contacts. '
        'Sub-bubbles inside each rule show the composition by order count and by billto count.',
        ha='center', va='top', fontsize=11.5, color=INK2)
ax.text(8.5, 9.55, f'Universe: {UNIVERSE:,} ordering contacts',
        ha='center', va='top', fontsize=10, color=MUTED, style='italic')

# --- BIG VENN CIRCLES ---
R2_CENTER = (5.0, 5.0); R4_CENTER = (12.0, 5.0)
BIG_R = 4.2
ax.add_patch(Circle(R2_CENTER, BIG_R, facecolor=R2_C, alpha=0.10,
                    edgecolor=R2_C, linewidth=2.5))
ax.add_patch(Circle(R4_CENTER, BIG_R, facecolor=R4_C, alpha=0.10,
                    edgecolor=R4_C, linewidth=2.5))

# --- RULE LABELS ---
# R2 (top-left)
ax.text(0.5, 8.9, 'Rule 2', color=R2_C, fontweight='bold', fontsize=19, ha='left')
ax.text(0.5, 8.48, 'Ship-to orders', color=INK, fontsize=13, ha='left')
ax.text(0.5, 8.13, 'Contacts who have placed',   color=INK2, fontsize=10, ha='left')
ax.text(0.5, 7.92, 'fewer than 3 orders at the',  color=INK2, fontsize=10, ha='left')
ax.text(0.5, 7.71, 'same ship-to location.',      color=INK2, fontsize=10, ha='left')
ax.text(0.5, 7.20, f'Blocks {R2_TOTAL:,} contacts',
        color=R2_C, fontweight='bold', fontsize=12, ha='left')
ax.text(0.5, 6.95, f'{R2_TOTAL/UNIVERSE*100:.1f}% of universe',
        color=INK2, fontsize=10, ha='left')

# R4 (top-right)
ax.text(16.5, 8.9, 'Rule 4', color=R4_C, fontweight='bold', fontsize=19, ha='right')
ax.text(16.5, 8.48, 'Multi-billto', color=INK, fontsize=13, ha='right')
ax.text(16.5, 8.13, 'Contacts who order across',   color=INK2, fontsize=10, ha='right')
ax.text(16.5, 7.92, 'more than one non-individual', color=INK2, fontsize=10, ha='right')
ax.text(16.5, 7.71, 'billing location.',            color=INK2, fontsize=10, ha='right')
ax.text(16.5, 7.20, f'Blocks {R4_TOTAL:,} contacts',
        color=R4_C, fontweight='bold', fontsize=12, ha='right')
ax.text(16.5, 6.95, f'{R4_TOTAL/UNIVERSE*100:.1f}% of universe',
        color=INK2, fontsize=10, ha='right')

# --- R2 SUB-BUBBLES ---
r2_positions = {
    '1 order in year':  (4.3, 5.0),
    '2 orders in year': (6.9, 6.0),
}

for name, contacts in r2_buckets:
    x, y = r2_positions[name]
    r = r_r2(contacts)
    ax.add_patch(Circle((x, y), r, facecolor=R2_BUB, alpha=0.92,
                        edgecolor='white', linewidth=1.6))
    if r >= 0.85:
        ax.text(x, y + 0.42, name, ha='center', va='center',
                color='white', fontsize=11, fontweight='bold', alpha=0.92)
        ax.text(x, y - 0.15, f'{contacts:,}', ha='center', va='center',
                color='white', fontsize=20, fontweight='bold')
    elif r >= 0.55:
        ax.text(x, y + 0.28, name, ha='center', va='center',
                color='white', fontsize=9.5, fontweight='bold', alpha=0.92)
        ax.text(x, y - 0.10, f'{contacts:,}', ha='center', va='center',
                color='white', fontsize=14, fontweight='bold')
    else:
        ax.text(x, y - r - 0.30, f'{name}\n{contacts:,}',
                ha='center', va='top', color=INK, fontsize=8)

# --- R4 SUB-BUBBLES ---
r4_positions = {
    '2 billtos':   (11.5, 4.7),
    '3–5 billtos': (13.9, 6.3),
    '6+ billtos':  (13.5, 3.3),
}

for name, contacts in r4_buckets:
    x, y = r4_positions[name]
    r = r_r4(contacts)
    ax.add_patch(Circle((x, y), r, facecolor=R4_BUB, alpha=0.92,
                        edgecolor='white', linewidth=1.6))
    if r >= 0.85:
        ax.text(x, y + 0.40, name, ha='center', va='center',
                color='white', fontsize=11, fontweight='bold', alpha=0.92)
        ax.text(x, y - 0.13, f'{contacts:,}', ha='center', va='center',
                color='white', fontsize=18, fontweight='bold')
    elif r >= 0.55:
        ax.text(x, y + 0.26, name, ha='center', va='center',
                color='white', fontsize=9.5, fontweight='bold', alpha=0.92)
        ax.text(x, y - 0.10, f'{contacts:,}', ha='center', va='center',
                color='white', fontsize=14, fontweight='bold')
    else:
        ax.text(x, y + 0.16, name, ha='center', va='center',
                color='white', fontsize=8, fontweight='bold', alpha=0.92)
        ax.text(x, y - 0.10, f'{contacts:,}', ha='center', va='center',
                color='white', fontsize=11, fontweight='bold')

# --- OVERLAP CALLOUT (in the lens) ---
lens_x = (R2_CENTER[0] + R4_CENTER[0]) / 2
ax.text(lens_x, 6.0, 'R2 ∩ R4', ha='center', va='center',
        color=OVERLAP, fontweight='bold', fontsize=11)
ax.text(lens_x, 5.55, f'~{BOTH_EST//1000}K', ha='center', va='center',
        color=OVERLAP, fontweight='bold', fontsize=22)
ax.text(lens_x, 5.15, 'contacts fail both', ha='center', va='center',
        color=OVERLAP, fontsize=10)
ax.text(lens_x, 4.90, '(estimated)', ha='center', va='center',
        color=MUTED, fontsize=8, style='italic')

# --- ELIGIBLE POOL FOOTER ---
ax.text(8.5, 0.95, 'Eligible pool',
        ha='center', va='center', fontsize=14, fontweight='bold', color=SWEET)
ax.text(8.5, 0.55, f'≈ {ELIGIBLE/1000:.0f}K contacts   ·   {ELIGIBLE/UNIVERSE*100:.0f}% of universe',
        ha='center', va='center', fontsize=12, color=INK)

# --- LEGEND NOTE ---
ax.text(0.5, 0.30,
        'Bubble size ∝ contacts blocked, scaled per rule so each circle is filled.',
        ha='left', va='center', fontsize=9, color=MUTED, style='italic')

fig.savefig('/home/user/scheduling/venn_contact_11x17.pdf',
            bbox_inches='tight', pad_inches=0.20)
fig.savefig('/home/user/scheduling/venn_contact_11x17.png',
            dpi=200, bbox_inches='tight', pad_inches=0.20)
plt.close(fig)
print("Saved venn_contact_11x17.pdf and .png")
