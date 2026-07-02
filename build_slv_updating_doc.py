"""Build the Word one-pager: 'Updating Shipping Location View Rules'."""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = '/home/user/scheduling/Updating_SLV_Rules.docx'

BRAND       = RGBColor(0x2F, 0x4A, 0x7C)
INK         = RGBColor(0x1A, 0x1A, 0x1A)
INK_2       = RGBColor(0x55, 0x55, 0x55)
HIGHLIGHT   = 'FDF3D3'
BRAND_FILL  = '2F4A7C'
ROW_ALT     = 'F6F7FA'

doc = Document()

# Landscape letter
section = doc.sections[0]
section.orientation = WD_ORIENT.LANDSCAPE
section.page_width  = Inches(11)
section.page_height = Inches(8.5)
section.left_margin = section.right_margin = Inches(0.75)
section.top_margin  = section.bottom_margin = Inches(0.6)

body_style = doc.styles['Normal']
body_style.font.name = 'Calibri'
body_style.font.size = Pt(11)

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

def cell_text(cell, text, bold=False, color=INK, size=10.5, align='left', fill=None):
    cell.text = ''
    para = cell.paragraphs[0]
    para.paragraph_format.space_before = Pt(0)
    para.paragraph_format.space_after = Pt(0)
    if align == 'right':   para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    elif align == 'center':para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:                  para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = para.add_run(text)
    run.font.size = Pt(size); run.bold = bold; run.font.color.rgb = color
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    set_cell_borders(cell)
    if fill: set_cell_shading(cell, fill)

def set_row_height(row, points, rule='atLeast'):
    tr_pr = row._tr.get_or_add_trPr()
    height = OxmlElement('w:trHeight')
    height.set(qn('w:val'), str(int(points * 20)))
    height.set(qn('w:hRule'), rule)
    tr_pr.append(height)

# --- TITLE ---
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(12)
pPr = p._p.get_or_add_pPr()
pBdr = OxmlElement('w:pBdr')
bottom = OxmlElement('w:bottom')
bottom.set(qn('w:val'), 'single'); bottom.set(qn('w:sz'), '8'); bottom.set(qn('w:color'), '2F4A7C')
pBdr.append(bottom); pPr.append(pBdr)
r = p.add_run('Updating Shipping Location View Rules')
r.bold = True; r.font.size = Pt(20); r.font.color.rgb = BRAND

# --- INTRO (VP voice, business context) ---
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(16)
r = p.add_run(
    'We introduced Shipping Location View in 2017 to let coworkers at the same shipping '
    'location see one another’s order history. The eligibility rules have not been revisited '
    'since. Given the reordering benefits we see from customers with shared order history '
    'and purple links, we recommend revisiting the combination of rules to open shared view '
    'to more customers.'
)
r.font.size = Pt(11)

# --- SECTION 1 ---
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(2); p.paragraph_format.space_after = Pt(4)
r = p.add_run('1. Raising the Contact-Count Threshold')
r.bold = True; r.font.size = Pt(14); r.font.color.rgb = BRAND

p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(6)
p.add_run(
    'The current rule excludes any customer location with 10 or more active ordering contacts. '
    'The table shows how many additional customer locations and orders each higher threshold '
    'would include, and what would remain excluded even at 50 contacts.'
).font.size = Pt(11)

hdr = ['Threshold', 'Eligible CMFs', '% CMFs',
       'Eligible Orders (cumulative)', 'Marginal Orders (Δ)', '% of Orders']
rows_r1 = [
    ('10 (current)', '532,692', '97.7%', '12,696,477', 'baseline',  '74.8%', False),
    ('12',           '536,042', '98.4%', '13,207,047', '+510,570',  '77.8%', False),
    ('15',           '538,906', '98.9%', '13,717,234', '+510,187',  '80.8%', False),
    ('20',           '541,297', '99.3%', '14,226,992', '+509,758',  '83.8%', False),
    ('25',           '542,518', '99.5%', '14,554,315', '+327,323',  '85.7%', False),
    ('50',           '544,279', '99.9%', '15,232,307', '+678,000',  '89.7%', False),
    ('50+ (stays out)', '751',   '0.1%', '—',      '1,752,777','10.3%', True),
]
t = doc.add_table(rows=1 + len(rows_r1), cols=6)
t.alignment = WD_TABLE_ALIGNMENT.LEFT
col_widths = [Inches(1.5), Inches(1.4), Inches(1.0), Inches(2.0), Inches(1.7), Inches(1.1)]
for i, w in enumerate(col_widths):
    t.columns[i].width = w
    for cell in t.columns[i].cells:
        cell.width = w
for i, h in enumerate(hdr):
    cell = t.rows[0].cells[i]
    cell_text(cell, h, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF), size=10.5,
              align='right' if i > 0 else 'left', fill=BRAND_FILL)
set_row_height(t.rows[0], 22)
for ri, row_data in enumerate(rows_r1, 1):
    fill = HIGHLIGHT if row_data[-1] else (ROW_ALT if ri % 2 == 0 else None)
    for ci, val in enumerate(row_data[:-1]):
        cell = t.rows[ri].cells[ci]
        cell_text(cell, val, bold=(row_data[-1] and ci == 0),
                  color=INK, size=10.5,
                  align='right' if ci > 0 else 'left', fill=fill)
    set_row_height(t.rows[ri], 20)

# --- SECTION 2 ---
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(16); p.paragraph_format.space_after = Pt(4)
r = p.add_run('2. Excluded List Codes')
r.bold = True; r.font.size = Pt(14); r.font.color.rgb = BRAND

p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(6)
p.add_run(
    'The list codes below are excluded from Shipping Location View outright. '
    'For each, the table shows how many customer locations would already meet the '
    'contact-count rule (fewer than 10) versus those that would still be excluded on it.'
).font.size = Pt(11)

hdr2 = ['List Code', 'Category',
        'Total CMFs', 'Eligible (<10)', 'Ineligible (10+)', 'Total Orders']

# (list_code, category, total_cmfs, elig_cmfs, inelig_cmfs, total_orders, highlight)
rows_r3 = [
    ('05', 'Federal Government (Domestic)',       3032,  2924,   108,   58169, False),
    ('06', 'Federal Government (APO/FPO)',         186,   185,     1,     786, False),
    ('07', 'State Government',                    6798,  6282,   516,  184911, False),
    ('08', 'Municipal / Private Institute',      16009, 15787,   222,  222199, False),
    ('09', 'Private College / University',        2423,  2160,   263,  112332, False),
    ('15', 'McMaster-Carr Internal',                 5,     0,     5,   42130, True),
    ('—', 'Total',                          28453, 27338,  1115,  620527, True),
]

t2 = doc.add_table(rows=1 + len(rows_r3), cols=6)
t2.alignment = WD_TABLE_ALIGNMENT.LEFT
col_widths_2 = [Inches(1.0), Inches(3.0), Inches(1.3), Inches(1.4), Inches(1.4), Inches(1.6)]
for i, w in enumerate(col_widths_2):
    t2.columns[i].width = w
    for cell in t2.columns[i].cells:
        cell.width = w

for i, h in enumerate(hdr2):
    cell = t2.rows[0].cells[i]
    cell_text(cell, h, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF), size=10.5,
              align='right' if i >= 2 else 'left', fill=BRAND_FILL)
set_row_height(t2.rows[0], 22)

for ri, row_data in enumerate(rows_r3, 1):
    highlight = row_data[-1]
    fill = HIGHLIGHT if highlight else (ROW_ALT if ri % 2 == 0 else None)
    vals = [
        row_data[0], row_data[1],
        f'{row_data[2]:,}', f'{row_data[3]:,}', f'{row_data[4]:,}', f'{row_data[5]:,}',
    ]
    for ci, val in enumerate(vals):
        cell = t2.rows[ri].cells[ci]
        bold = highlight and ci >= 1
        cell_text(cell, val, bold=bold, color=INK, size=10.5,
                  align='right' if ci >= 2 else 'left', fill=fill)
    set_row_height(t2.rows[ri], 20)

doc.save(OUT)
print(f'Saved → {OUT}')
