"""Build the Word one-pager: 'Updating Shipping Location View Rules'.
Format modeled on slv_sprint_analysis_v2.pdf — blue headings, blue table headers,
cream highlight rows.
"""
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = '/home/user/scheduling/Updating_SLV_Rules.docx'

BRAND       = RGBColor(0x2F, 0x4A, 0x7C)   # deep blue for headings
BRAND_DARK  = RGBColor(0x1F, 0x3A, 0x6C)
INK         = RGBColor(0x1A, 0x1A, 0x1A)
INK_2       = RGBColor(0x55, 0x55, 0x55)
MUTED       = RGBColor(0x88, 0x88, 0x88)
HIGHLIGHT   = 'FDF3D3'   # cream highlight fill
BRAND_FILL  = '2F4A7C'   # table header fill
ROW_ALT     = 'F6F7FA'   # zebra fill

doc = Document()

# Page setup: portrait letter, tight margins
for section in doc.sections:
    section.left_margin = section.right_margin = Inches(0.7)
    section.top_margin = section.bottom_margin = Inches(0.55)

body_style = doc.styles['Normal']
body_style.font.name = 'Calibri'
body_style.font.size = Pt(10.5)

# ---------- helpers ----------
def set_cell_shading(cell, hex_fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:fill'), hex_fill)
    shd.set(qn('w:val'), 'clear')
    tc_pr.append(shd)

def set_cell_borders(cell, size=6, color='B0B7C3'):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement('w:tcBorders')
    for edge in ('top', 'left', 'bottom', 'right'):
        b = OxmlElement(f'w:{edge}')
        b.set(qn('w:val'), 'single')
        b.set(qn('w:sz'), str(size))
        b.set(qn('w:color'), color)
        borders.append(b)
    tc_pr.append(borders)

def cell_text(cell, text, bold=False, color=INK, size=10, align='left',
              italic=False, fill=None):
    cell.text = ''
    para = cell.paragraphs[0]
    if align == 'right':
        para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    elif align == 'center':
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = para.add_run(text)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = color
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    set_cell_borders(cell)
    if fill:
        set_cell_shading(cell, fill)

def add_heading_h1(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(20)
    run.font.color.rgb = BRAND
    return p

def add_subtitle(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(10)
    # bottom border on this paragraph
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '12')
    bottom.set(qn('w:color'), '2F4A7C')
    pBdr.append(bottom)
    pPr.append(pBdr)
    run = p.add_run(text)
    run.italic = False
    run.font.size = Pt(11)
    run.font.color.rgb = INK_2
    return p

def add_heading_h2(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(13.5)
    run.font.color.rgb = BRAND
    return p

def add_lede(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(8)
    run = p.add_run(text)
    run.font.size = Pt(10.5)
    run.font.color.rgb = INK_2
    return p

def add_body(text, italic=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    run.font.size = Pt(10.5)
    run.italic = italic
    run.font.color.rgb = INK
    return p

def set_row_height(row, points):
    tr_pr = row._tr.get_or_add_trPr()
    height = OxmlElement('w:trHeight')
    height.set(qn('w:val'), str(int(points * 20)))
    height.set(qn('w:hRule'), 'atLeast')
    tr_pr.append(height)

# =============================================================================
# TITLE + SUBTITLE
# =============================================================================
add_heading_h1('Updating Shipping Location View Rules')
add_subtitle('Follow-up to the sprint eligibility analysis')

# =============================================================================
# INTRO (placeholder)
# =============================================================================
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(12)
run = p.add_run(
    '[Intro paragraph — one paragraph of McMaster-Carr voice framing the two '
    'decisions we are bringing forward: (1) loosening the R1 contact-count '
    'threshold, and (2) narrowing the R3 listcode exclusion after evaluating '
    'each listcode by contact-count profile.]'
)
run.italic = True
run.font.color.rgb = MUTED
run.font.size = Pt(10.5)

# Starting universe callout (light blue bar)
callout_tbl = doc.add_table(rows=1, cols=3)
callout_tbl.autofit = False
callout_tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
widths = [Inches(2.4), Inches(2.9), Inches(1.8)]
for i, w in enumerate(widths):
    callout_tbl.columns[i].width = w
cells = callout_tbl.rows[0].cells

def kpi_cell(cell, lbl, val):
    cell.text = ''
    p1 = cell.paragraphs[0]
    r1 = p1.add_run(lbl.upper() + '\n')
    r1.font.size = Pt(8.5)
    r1.bold = True
    r1.font.color.rgb = BRAND
    r2 = p1.add_run(val)
    r2.font.size = Pt(11.5)
    r2.bold = True
    r2.font.color.rgb = INK
    set_cell_shading(cell, 'E6ECF4')
    # left border only on first cell (accent)
    tc_pr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ('top', 'bottom', 'right'):
        b = OxmlElement(f'w:{edge}'); b.set(qn('w:val'), 'nil'); tcBorders.append(b)
    tc_pr.append(tcBorders)

kpi_cell(cells[0], 'Starting universe', '566,092 CMFs')
kpi_cell(cells[1], 'After Action 1 · distributor removed', '545,030 CMFs · 16.99M orders')
kpi_cell(cells[2], 'Window', '3/12/2025 – 3/12/2026')

# add left accent border to first cell
tc_pr = cells[0]._tc.get_or_add_tcPr()
tcBorders = OxmlElement('w:tcBorders')
for edge in ('top', 'bottom', 'right'):
    b = OxmlElement(f'w:{edge}'); b.set(qn('w:val'), 'nil'); tcBorders.append(b)
left = OxmlElement('w:left'); left.set(qn('w:val'), 'single'); left.set(qn('w:sz'), '24'); left.set(qn('w:color'), '2F4A7C')
tcBorders.append(left)
tc_pr.append(tcBorders)

doc.add_paragraph().paragraph_format.space_after = Pt(4)

# =============================================================================
# SECTION 1 — R1 THRESHOLD SENSITIVITY
# =============================================================================
add_heading_h2('1. R1 Threshold Sensitivity')
add_lede(
    'R1 currently excludes CMFs with 10 or more active ordering contacts. Cumulative view shows '
    'what each step-up admits; the final row is the residual tail that stays out even at threshold 50.'
)

hdr = ['Threshold', 'Eligible CMFs', '% CMFs',
       'Eligible Orders\n(cumulative)', 'Marginal Orders (Δ)', '% of Orders']
rows_r1 = [
    ('10 (current)', '532,692', '97.7%', '12,696,477', 'baseline',  '74.8%', False),
    ('12',           '536,042', '98.4%', '13,207,047', '+510,570',  '77.8%', False),
    ('15',           '538,906', '98.9%', '13,717,234', '+510,187',  '80.8%', False),
    ('20',           '541,297', '99.3%', '14,226,992', '+509,758',  '83.8%', False),
    ('25',           '542,518', '99.5%', '14,554,315', '+327,323',  '85.7%', False),
    ('50',           '544,279', '99.9%', '15,232,307', '+678,000',  '89.7%', False),
    ('50+ (stays out)', '751',   '0.1%', '—',           '1,752,777','10.3%', True),
]
t = doc.add_table(rows=1 + len(rows_r1), cols=6)
t.alignment = WD_TABLE_ALIGNMENT.LEFT
col_widths = [Inches(1.4), Inches(1.15), Inches(0.75), Inches(1.5), Inches(1.35), Inches(0.85)]
for i, w in enumerate(col_widths):
    t.columns[i].width = w
# header
for i, h in enumerate(hdr):
    cell = t.rows[0].cells[i]
    cell_text(cell, h, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF), size=9.5,
              align='right' if i > 0 else 'left', fill=BRAND_FILL)
set_row_height(t.rows[0], 26)
# body
for ri, row_data in enumerate(rows_r1, 1):
    fill = HIGHLIGHT if row_data[-1] else (ROW_ALT if ri % 2 == 0 else None)
    for ci, val in enumerate(row_data[:-1]):
        cell = t.rows[ri].cells[ci]
        bold = row_data[-1] and ci == 0
        color = BRAND if (ci == 4 and ri < 7) else INK   # marginal column in brand blue for cum rows
        if row_data[-1]:
            color = INK
        cell_text(cell, val, bold=bold, color=color, size=10,
                  align='right' if ci > 0 else 'left', fill=fill)

# footnote
p_foot = doc.add_paragraph()
p_foot.paragraph_format.space_after = Pt(6)
r = p_foot.add_run(
    'Density climbs at every step (152 → 178 → 213 → 268 → 385 orders per added CMF). '
    'The 751 CMFs above 50 contacts still cover 10% of orders — they will never qualify on contact count alone.'
)
r.italic = True; r.font.size = Pt(9.5); r.font.color.rgb = MUTED

# =============================================================================
# SECTION 2 — R3 LISTCODE × ELIGIBLE / INELIGIBLE
# =============================================================================
add_heading_h2('2. R3 Listcodes · CMFs and Orders by Contact-Count Range')
add_lede(
    'For each R3-excluded listcode, CMFs and orders split by active-contact range: <10 would already pass R1, '
    '10–25 is the recoverable middle, 25+ is the never-eligible tail. Distributor removed per Action 1.'
)

hdr2 = ['Listcode', 'Category',
        'Total\nCMFs', 'CMFs\n<10', 'CMFs\n10–25', 'CMFs\n25+',
        'Total\nOrders', 'Orders\n<10', 'Orders\n10–25', 'Orders\n25+']

# (listcode, category, total_cmfs, cmfs_lt10, cmfs_10_25, cmfs_gt25,
#  total_orders, orders_lt10, orders_10_25, orders_gt25, highlight)
rows_r3 = [
    ('05', 'Federal Gov (Domestic)',
        3032,  2924,   87,  21,   58169,  23278,  11401,  23490, False),
    ('06', 'Federal Gov (APO/FPO)',
         186,   185,    1,   0,     786,    705,     81,      0, False),
    ('07', 'State Gov',
        6798,  6282,  382, 134,  184911,  86816,  43295,  54800, False),
    ('08', 'Municipal / Private Institute',
       16009, 15787,  176,  46,  222199, 151639,  22623,  47937, False),
    ('09', 'Private College / University',
        2423,  2160,  171,  92,  112332,  32102,  17286,  62944, False),
    ('15', 'McMaster-Carr internal (excluded)',
           5,     0,    0,   5,   42130,      0,      0,  42130, True),
    ('—',  'R3 TOTAL (ex-distributor)',
       28453, 27338,  817, 298,  620527, 294540,  94686, 231301, True),
]

t2 = doc.add_table(rows=1 + len(rows_r3), cols=10)
t2.alignment = WD_TABLE_ALIGNMENT.LEFT
col_widths_2 = [Inches(0.45), Inches(1.6), Inches(0.6),
                Inches(0.55), Inches(0.6), Inches(0.55),
                Inches(0.75), Inches(0.65), Inches(0.7), Inches(0.65)]
for i, w in enumerate(col_widths_2):
    t2.columns[i].width = w

# header row
for i, h in enumerate(hdr2):
    cell = t2.rows[0].cells[i]
    cell_text(cell, h, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF), size=8.5,
              align='right' if i >= 2 else 'left', fill=BRAND_FILL)
set_row_height(t2.rows[0], 30)

for ri, row_data in enumerate(rows_r3, 1):
    highlight = row_data[-1]
    fill = HIGHLIGHT if highlight else (ROW_ALT if ri % 2 == 0 else None)
    vals = [
        row_data[0],                      # listcode
        row_data[1],                      # category
        f'{row_data[2]:,}',               # total cmfs
        f'{row_data[3]:,}',               # cmfs <10
        f'{row_data[4]:,}',               # cmfs 10-25
        f'{row_data[5]:,}',               # cmfs 25+
        f'{row_data[6]:,}',               # total orders
        f'{row_data[7]:,}',               # orders <10
        f'{row_data[8]:,}',               # orders 10-25
        f'{row_data[9]:,}',               # orders 25+
    ]
    for ci, val in enumerate(vals):
        cell = t2.rows[ri].cells[ci]
        bold = (ci == 1 and highlight) or (highlight and ci >= 2)
        cell_text(cell, val, bold=bold, color=INK, size=9,
                  align='right' if ci >= 2 else 'left', fill=fill)

# footnote
p_foot2 = doc.add_paragraph()
p_foot2.paragraph_format.space_after = Pt(2)
r = p_foot2.add_run(
    '96% of R3-excluded CMFs are already R1-eligible (<10 contacts) but carry only 48% of the blocked orders. '
    'The 25+ tail — under 300 CMFs — carries 231K orders. '
    'Listcode 15 is 100% in the 25+ bucket because it is McMaster-Carr\'s own five branches (500–1,700 employees each).'
)
r.italic = True; r.font.size = Pt(9.5); r.font.color.rgb = MUTED

# =============================================================================
# COLOPHON
# =============================================================================
doc.add_paragraph().paragraph_format.space_before = Pt(6)
p_col = doc.add_paragraph()
pPr = p_col._p.get_or_add_pPr()
pBdr = OxmlElement('w:pBdr')
top = OxmlElement('w:top')
top.set(qn('w:val'), 'single'); top.set(qn('w:sz'), '4'); top.set(qn('w:color'), 'C8C2B0')
pBdr.append(top); pPr.append(pBdr)
r = p_col.add_run(
    'Source: secure.order_source · Universe: CMFs that placed ≥1 order in window · '
    'ex-three shared credit-card CMFs · Contact counts and listcodes as of 12-month window.'
)
r.italic = True; r.font.size = Pt(9); r.font.color.rgb = MUTED

doc.save(OUT)
print(f'Saved → {OUT}')
