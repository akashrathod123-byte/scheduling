"""Build 11x17 landscape PDF with 3 Venn diagrams side by side.

Layout note: keep the original simple 1x3 subplot layout with
`bbox_inches='tight'` on save — that version printed cleanly at 11x17.
The header context text sits above the subplots as figure-level text so
the tight bbox includes it without disturbing the diagram layout.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import matplotlib as mpl

# Colors
R3, R4, R1, R2 = '#a63a48', '#e5983f', '#3b6e8a', '#6f4859'
INK, INK_2, MUTED = '#1a1a1a', '#4a4a4a', '#8a8a8a'

mpl.rcParams['font.family'] = 'DejaVu Sans'

venns = [
    dict(
        title='Orders Blocked',
        universe='Universe: 17M orders placed in a 12-month window',
        regions=dict(
            r3_only='787K', r4_only='1.32M',
            r1_only='3.32M', r2_only='565K',
            r3_r4='82K', r1_r2='149K',
            r3_r1='208K', r4_r2='59K',
            center='435K',
        ),
        totals='R1: 4.08M   R2: 835K   R3: 1.16M   R4: 1.86M',
        descs={
            'R3': ('Orders at shipping locations', 'with excluded list codes.'),
            'R4': ('Orders by contacts using', 'more than one non-individual billto.'),
            'R1': ('Orders at shipping locations', 'with 10+ active contacts.'),
            'R2': ('Orders by contacts with <3', 'orders at the same ship-to.'),
        },
    ),
    dict(
        title='Contacts Affected',
        universe=('Universe: There are 1.39M total contacts.\n'
                  'From these, 500K have placed an order in the 12-month window.'),
        regions=dict(
            r3_only='46K', r4_only='18K',
            r1_only='125K', r2_only='449K',
            r3_r4='1.5K', r1_r2='98K',
            r3_r1='10K', r4_r2='15K',
            center='53K',
        ),
        totals='R1: 248K   R2: 611K   R3: 103K   R4: 43K',
        descs={
            'R3': ('Contacts at a shipping location', 'with an excluded list code.'),
            'R4': ('Contacts who use more than one', 'non-individual billing location.'),
            'R1': ('Contacts at a shipping location', 'with 10+ active contacts.'),
            'R2': ('Contacts with <3 orders', 'at the same ship-to location.'),
        },
    ),
    dict(
        title='Shipping Locations (CMFs)',
        universe=('Universe: 555K of 1.15M CMFs that placed an order in the 12-month window.\n'
                  'A CMF is counted if the rule applies to any contact.'),
        regions=dict(
            r3_only='78K', r4_only='46K',
            r1_only='8.7K', r2_only='212K',
            r3_r4='5K', r1_r2='2K',
            r3_r1='1.4K', r4_r2='13K',
            center='24K',
        ),
        totals='R1: 13K   R2: 251K   R3: 107K   R4: 66K',
        descs={
            'R3': ('Shipping locations with', 'excluded list codes.'),
            'R4': ('Shipping locations with a contact', 'using >1 non-individual billto.'),
            'R1': ('Shipping locations with 10+', 'active ordering contacts.'),
            'R2': ('Shipping locations with a contact', 'with <3 orders at that ship-to.'),
        },
    ),
]

fig = plt.figure(figsize=(17, 11), dpi=100)
fig.patch.set_facecolor('white')

# --- HEADER CONTEXT (figure-level text; bbox_inches='tight' includes it) ---
fig.text(0.03, 0.985, 'Shipping Location View  ·  Compounding-Rule Impact',
         ha='left', va='top', fontsize=17, fontweight='bold', color=INK)

fig.text(0.03, 0.935,
         "Today, ~471,000 contacts have access to Shipping Location View. "
         "97.7% (~460K) were enrolled automatically by the algorithm; "
         "2.3% (~10,700) were added manually by Customer Service.",
         ha='left', va='top', fontsize=11, color=INK)

fig.text(0.03, 0.88,
         "Each diagram below shows the volume excluded by each of the four eligibility rules —\n"
         "measured in orders, contacts, and CMFs. Each circle represents one of the four eligibility\n"
         "rules, and the overlaps are when multiple rules apply.",
         ha='left', va='top', fontsize=11, color=INK, linespacing=1.45)

# Reserve top space for header, then let bbox_inches='tight' trim the sides.
plt.subplots_adjust(top=0.78, bottom=0.02, left=0.02, right=0.98, wspace=0.05)

for i, venn in enumerate(venns):
    ax = fig.add_subplot(1, 3, i + 1)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14)
    ax.set_aspect('equal')
    ax.axis('off')

    # Title + universe
    ax.text(5, 13.5, venn['title'], ha='center', va='center',
            fontsize=15, fontweight='bold', color=INK)
    ax.text(5, 12.9, venn['universe'], ha='center', va='center',
            fontsize=8.5, color=INK_2, style='italic', linespacing=1.4)

    # 4 circles (r=2.3 · centers spaced 2.6 apart)
    positions = {
        'R3': (3.7, 9, R3), 'R4': (6.3, 9, R4),
        'R1': (3.7, 6, R1), 'R2': (6.3, 6, R2),
    }
    for _, (cx, cy, color) in positions.items():
        ax.add_patch(Circle((cx, cy), 2.3, color=color, alpha=0.72, edgecolor='none'))

    # Rule labels in the four corners
    def rlabel(x, y, name, subname, color, ha, descs):
        ax.text(x, y, name, color=color, fontweight='bold', fontsize=11, ha=ha, va='top')
        ax.text(x, y - 0.42, subname, color=INK, fontsize=9, ha=ha, va='top')
        for j, line in enumerate(descs):
            ax.text(x, y - 0.95 - j * 0.36, line, color=INK_2, fontsize=7.5, ha=ha, va='top')

    rlabel(0.2, 12.0, 'Rule 3', 'Listcode', R3, 'left',  venn['descs']['R3'])
    rlabel(9.8, 12.0, 'Rule 4', 'Multi-billto', R4, 'right', venn['descs']['R4'])
    rlabel(0.2, 3.5,  'Rule 1', 'Contact count', R1, 'left',  venn['descs']['R1'])
    rlabel(9.8, 3.5,  'Rule 2', 'Ship-to orders', R2, 'right', venn['descs']['R2'])

    # Region numbers with tiny caption
    def rn(x, y, val, tag, size=12):
        ax.text(x, y, val, ha='center', va='center', color='white',
                fontweight='bold', fontsize=size)
        ax.text(x, y - 0.42, tag, ha='center', va='center', color='white',
                fontsize=6.5, alpha=0.9)

    # 4 "only" regions
    rn(2.7, 9.3, venn['regions']['r3_only'], 'R3 ONLY', size=13)
    rn(7.3, 9.3, venn['regions']['r4_only'], 'R4 ONLY', size=13)
    rn(2.7, 5.7, venn['regions']['r1_only'], 'R1 ONLY', size=13)
    rn(7.3, 5.7, venn['regions']['r2_only'], 'R2 ONLY', size=13)
    # 4 pair overlaps
    rn(5.0, 9.15, venn['regions']['r3_r4'], 'R3 ∩ R4', size=10)
    rn(5.0, 5.85, venn['regions']['r1_r2'], 'R1 ∩ R2', size=10)
    rn(3.7, 7.5,  venn['regions']['r3_r1'], 'R3 ∩ R1', size=10)
    rn(6.3, 7.5,  venn['regions']['r4_r2'], 'R4 ∩ R2', size=10)
    # Center
    rn(5.0, 7.5, venn['regions']['center'], '3+ RULES', size=9)

    # Footer totals
    ax.text(5, 0.7, venn['totals'], ha='center', va='center',
            fontsize=8.5, color=MUTED)

fig.savefig('/home/user/scheduling/slv_venn_11x17.pdf', bbox_inches='tight', pad_inches=0.3)
fig.savefig('/home/user/scheduling/slv_venn_11x17.png', dpi=200, bbox_inches='tight', pad_inches=0.3)
plt.close(fig)
print("Saved slv_venn_11x17.pdf and .png")
