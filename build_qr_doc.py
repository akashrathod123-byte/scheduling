"""QR Code Summary — McMaster business voice, language pass."""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

OUT = '/home/user/scheduling/QR_Code_Visit_Summary.docx'

doc = Document()

for s in doc.sections:
    s.left_margin = s.right_margin = Inches(1.0)
    s.top_margin = s.bottom_margin = Inches(0.9)

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
    para = doc.add_paragraph()
    run = para.add_run(text); run.bold = True
    run.font.size = Pt(13); run.underline = True
    para.paragraph_format.space_before = Pt(before)
    para.paragraph_format.space_after = Pt(after)
    return para

def bullet(text, size=11):
    para = doc.add_paragraph(text, style='List Bullet')
    for run in para.runs: run.font.size = Pt(size)
    para.paragraph_format.space_after = Pt(2)
    return para

# ── TITLE ───────────────────────────────────────────────────────────────────
title = doc.add_paragraph()
tr = title.add_run('QR Codes on Prepack Items')
tr.bold = True; tr.font.size = Pt(16); tr.underline = True
title.paragraph_format.space_after = Pt(2)

sub = doc.add_paragraph()
sr = sub.add_run('January 21 – May 28, 2026')
sr.font.size = Pt(11); sr.italic = True
sub.paragraph_format.space_after = Pt(14)

# ── BACKGROUND ──────────────────────────────────────────────────────────────
h('Background', before=0)
p("In January, Prepack items started to include modern McMaster-Carr branding "
  "and a QR code on every label. The QR code takes customers directly to "
  "the part's product detail page on McMaster.com, making reordering easier for "
  "customers who have the part in hand.")
p("172 customers have scanned a Prepack code since launch. Weekly volume is climbing, "
  "about half of scans match to a known customer account, and a handful of parts "
  "are getting scanned repeatedly.")

# ── HOW WE MEASURED ─────────────────────────────────────────────────────────
h('How we measured it')
para = doc.add_paragraph()
para.paragraph_format.space_after = Pt(4)
r1 = para.add_run("Every Prepack QR code points to a McMaster.com URL with the same "
                  "format: the part number, followed by a short tag ("); r1.font.size = Pt(11)
r2 = para.add_run("mode=QR & codeid=4");                                  r2.font.size = Pt(11); r2.bold = True
r3 = para.add_run(") that identifies it as a Prepack scan. We pulled every visit "
                  "that landed on one of these URLs between January 21 and May 28."); r3.font.size = Pt(11)
p("We filtered out scans associated with our internal IP addresses, and dropped "
  "visits with no recorded activity. That left 172 customer scans.")

# ── VOLUME ──────────────────────────────────────────────────────────────────
h('QR scan volume')
p("Volume has grown steadily. Weekly scans averaged about 3 in February. By May, "
  "weekly scans ranged from 9 to 27, with the high the week of May 18.")
doc.add_picture('/home/user/scheduling/qr_weekly.png', width=Inches(6.5))

# ── WHO'S SCANNING ──────────────────────────────────────────────────────────
h('Who is scanning')
p("Most customers scan without being logged in, so the visit alone doesn't tell us "
  "who they are. We matched scans to known customers using two signals: the anonymous "
  "visitor ID tied to each visit, and the IP address the scan came from.")
p("About half — 90 of the 172 scans — matched to a known customer this way. The "
  "matches skew toward shops and credit-card buyers reordering specific parts.")

# ── WHAT THEY DO ────────────────────────────────────────────────────────────
h('What customers do after they scan')
p("Most scans are short. About seven in ten customers land on the part page and "
  "leave without taking any further action.")
p("The remaining 31% went deeper. They filtered specs, expanded images, opened "
  "related parts, and came back to the scanned product later in the visit. Three "
  "placed items in their order pad. One downloaded a CAD file.")

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
        c = t.rows[ri].cells[ci]; c.text = ''
        r = c.paragraphs[0].add_run(v); r.font.size = Pt(11)

p('', after=6)
p("92% of scans came from a phone — roughly 60% iPhone and 40% Android. The "
  "remaining 8% came from desktop browsers, usually a customer who scanned with "
  "their phone and finished the visit on a computer.")

# ── PARTS ───────────────────────────────────────────────────────────────────
h('Which parts get scanned')
p("Customers scanned 127 different part numbers. About three-quarters (98 of the "
  "127) were scanned only once. Twenty-nine were scanned more than once.")

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
        c = t2.rows[ri].cells[ci]; c.text = ''
        r = c.paragraphs[0].add_run(v); r.font.size = Pt(11)

# ── NOTABLE VISITS ──────────────────────────────────────────────────────────
h('Notable visits')
p("Four visits worth a closer look:")

p('Henkels & McCoy — visit 6e77d3a6918e42b2845a410daa567c3b',
  bold=True, size=11, before=4, after=2)
p("Customer scanned the code for part 92188A145 (a stainless brass tapping insert) "
  "on a mobile device. Within eight minutes, they adjusted the quantity to 7 and "
  "placed an order for $489.11 with same-day delivery.")

p('Fathom & Form LLC — visit 84e1a820d4b242d0a82961091c4f4043',
  bold=True, size=11, before=8, after=2)
p("Customer scanned the code for part 90764A330 on May 11 and added one unit to a "
  "preorder within five seconds of landing. Same-day pickup was available in Santa "
  "Fe Springs.")

p('Unknown customer — visit 074c5848af5345be847a34d202010652',
  bold=True, size=11, before=8, after=2)
p("Customer scanned the code, went straight to Order History, and added part "
  "91251A440 to a new order. A clean reorder flow.")

p('CAD download — visit 48e0af17c2974d60b136232fd9f55bff',
  bold=True, size=11, before=8, after=2)
p("Customer scanned the code for part 91812A215 (an extreme-vibration wedge lock "
  "washer) and downloaded the CAD file within 25 seconds. Likely an engineering "
  "use case rather than a reorder.")

# ── TAKEAWAYS ───────────────────────────────────────────────────────────────
h('Takeaways')
bullet("Volume is climbing. Weekly scans in May ran roughly five times higher than "
       "in February. We expect continued growth as more Prepacks ship.")
bullet("About half of scans match to a known customer account.")
bullet("Most scans are short. The 31% who go deeper engage meaningfully — filtering "
       "specs, expanding images, and in some cases adding items to the order pad.")
bullet("Twenty-nine parts came up more than once. These are worth a closer look as "
       "we think about better labeling, reorder prompts, or new packaging formats.")

doc.save(OUT)
print(f"Saved → {OUT}")
