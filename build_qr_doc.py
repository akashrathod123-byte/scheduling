"""QR Code Summary — McMaster business voice."""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

OUT = '/home/user/scheduling/QR_Code_Visit_Summary.docx'

doc = Document()

# Page setup — match reorder doc proportions
for s in doc.sections:
    s.left_margin = s.right_margin = Inches(1.0)
    s.top_margin = s.bottom_margin = Inches(0.9)

# Default body font
body_style = doc.styles['Normal']
body_style.font.name = 'Calibri'
body_style.font.size = Pt(11)

def p(text, bold=False, italic=False, size=11, before=0, after=4, align=None):
    para = doc.add_paragraph()
    if align is not None: para.alignment = align
    run = para.add_run(text)
    run.font.size = Pt(size); run.bold = bold; run.italic = italic
    para.paragraph_format.space_before = Pt(before)
    para.paragraph_format.space_after = Pt(after)
    return para

def h(text, before=14, after=4):
    """Heading style matching reorder doc — bold, underlined, plain size."""
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.bold = True
    run.font.size = Pt(13)
    run.underline = True
    para.paragraph_format.space_before = Pt(before)
    para.paragraph_format.space_after = Pt(after)
    return para

def bullet(text, size=11):
    para = doc.add_paragraph(text, style='List Bullet')
    for run in para.runs:
        run.font.size = Pt(size)
    para.paragraph_format.space_after = Pt(2)
    return para

# ── TITLE ───────────────────────────────────────────────────────────────────
title = doc.add_paragraph()
tr = title.add_run('QR Codes on Prepacks')
tr.bold = True; tr.font.size = Pt(16); tr.underline = True
title.paragraph_format.space_after = Pt(2)

sub = doc.add_paragraph()
sr = sub.add_run('January 21 – May 28, 2026   |   172 customer scans')
sr.font.size = Pt(11); sr.italic = True
sub.paragraph_format.space_after = Pt(14)

# ── BACKGROUND ──────────────────────────────────────────────────────────────
h('Background', before=0)
p("In January, packs created in Prepack began shipping with modern McMaster-Carr "
  "branding and a QR code on every label. The QR code takes customers directly to "
  "the part's product detail page on McMaster.com, making reordering easier for "
  "customers who have part in hand.")
p("From January 21 to date, there have been 172 customer scans in total. This report "
  "looks at who scanned, what they did, and which parts pulled the scans.")

# ── HOW WE MEASURED ─────────────────────────────────────────────────────────
h('How we measured it')
p("Every Prepack QR code encodes the same URL pattern: the part number in the path "
  "and ?mode=qr&codeid=4 as the query string. That signature let us isolate Prepack "
  "scans from regular product page traffic.")
p("Scan data came from the data warehouse and the interactions graph. Two cleaning passes:")
bullet("Internal McMaster-Carr scans were removed (test devices, internal IP ranges, "
       "and verification activity).")
bullet("Duplicate visits and visits with no recorded actions were dropped.")
p("172 unique customer scans remained.")

# ── VOLUME ──────────────────────────────────────────────────────────────────
h('Scan volume')
p("Volume grew steadily through the spring. February averaged roughly three scans "
  "per week. By May, weekly scans were averaging around seventeen, with a high of "
  "twenty-seven the week of May 18.")
doc.add_picture('/home/user/scheduling/qr_weekly.png', width=Inches(6.5))

# ── WHO'S SCANNING ──────────────────────────────────────────────────────────
h('Who is scanning')
p("Most customers who scan a QR code aren't logged in at the moment of the scan, "
  "so we don't get a clean customer ID for free. To work around this, we matched scans "
  "to known customers using three signals: the visitor ID stored in their browser, the "
  "session ID McMaster tracks for that visit, and the IP address the scan came from.")
p("Roughly half — 90 of the 172 scans — matched to a known customer this way. "
  "Most were small fabrication shops and credit-card buyers. The other half were "
  "first-time mobile visitors with no prior account history, or came from residential "
  "carrier IPs we couldn't tie to a specific account.")

# ── WHAT THEY DO ────────────────────────────────────────────────────────────
h('What customers do after they scan')
p("Most scans are short. About seven in ten customers land on the part page and leave "
  "without further interaction — typical behavior for QR codes in physical environments, "
  "where curious or accidental scans happen often.")
p("The remaining 31% went deeper. They filtered specs, expanded images, opened sibling "
  "parts, and revisited the scanned product. Three placed items in their order pad. One "
  "downloaded a CAD file.")

# Engagement table — simple, no fill colors
t = doc.add_table(rows=4, cols=3)
t.style = 'Table Grid'
hdr = t.rows[0].cells
for i, label in enumerate(['Visit length', 'Visits', '% of total']):
    hdr[i].text = ''
    r = hdr[i].paragraphs[0].add_run(label); r.bold = True; r.font.size = Pt(11)
rows_data = [
    ('Single action (landing only)',  '119', '69%'),
    ('2–5 actions',                    '41', '24%'),
    ('6+ actions',                     '12',  '7%'),
]
for ri, row in enumerate(rows_data, 1):
    for ci, v in enumerate(row):
        c = t.rows[ri].cells[ci]
        c.text = ''
        r = c.paragraphs[0].add_run(v); r.font.size = Pt(11)

p('', after=6)
p("92% of scans came from a phone — about 60% iPhone, 40% Android. The remaining 8% came "
  "from desktop browsers, typically a customer scanning into their phone and then continuing "
  "on a workstation.")

# ── PARTS ───────────────────────────────────────────────────────────────────
h('Which parts get scanned')
p("Customers scanned 127 different part numbers. Most parts (98 of the 127, or roughly "
  "three-quarters) were scanned only once. The parts scanned more than once are the "
  "clearest signal that the Prepack QR program is doing what we hoped — landing on a "
  "shop floor, getting used to reorder.")

t2 = doc.add_table(rows=12, cols=2)
t2.style = 'Table Grid'
hdr2 = t2.rows[0].cells
for i, label in enumerate(['Part number', 'Scans']):
    hdr2[i].text = ''
    r = hdr2[i].paragraphs[0].add_run(label); r.bold = True; r.font.size = Pt(11)
parts_data = [
    ('91251A242', '5'),
    ('95105A159', '5'),
    ('7073K332',  '4'),
    ('1095K11',   '3'),
    ('91247A628', '3'),
    ('92865A546', '3'),
    ('97467A117', '3'),
    ('92865A543', '3'),
    ('97802A316', '3'),
    ('91400A196', '3'),
    ('91000A469', '3'),
]
for ri, row in enumerate(parts_data, 1):
    for ci, v in enumerate(row):
        c = t2.rows[ri].cells[ci]
        c.text = ''
        r = c.paragraphs[0].add_run(v); r.font.size = Pt(11)

# ── TAKEAWAYS ───────────────────────────────────────────────────────────────
h('Takeaways')
bullet("Volume is climbing. Weekly scans are roughly five times higher in May than in "
       "February. We expect continued growth as more Prepacks ship.")
bullet("The customers we can identify are exactly who we hoped to reach — small shops "
       "and credit-card buyers reordering specific parts.")
bullet("Most scans are short, which is normal for physical QR codes. The 31% who engage "
       "show real purchase intent.")
bullet("The 29 parts scanned more than once tell us where the codes are being used most. "
       "These are good candidates for follow-up — better labeling, better reorder prompts, "
       "or new packaging formats.")

doc.save(OUT)
print(f"Saved → {OUT}")
