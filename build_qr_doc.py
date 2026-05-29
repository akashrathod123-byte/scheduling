"""Build director-friendly QR code summary document."""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = '/home/user/scheduling/QR_Code_Visit_Summary.docx'

doc = Document()

# Page margins
for s in doc.sections:
    s.left_margin = s.right_margin = Inches(0.9)
    s.top_margin = s.bottom_margin = Inches(0.8)

# ── styles helpers ──────────────────────────────────────────────────────────
def add_heading(text, level=1, color='1F4E79'):
    h = doc.add_paragraph()
    run = h.add_run(text)
    run.bold = True
    if level == 1:
        run.font.size = Pt(15); run.font.color.rgb = RGBColor.from_string(color)
        h.paragraph_format.space_before = Pt(14); h.paragraph_format.space_after = Pt(4)
    else:
        run.font.size = Pt(12); run.font.color.rgb = RGBColor.from_string(color)
        h.paragraph_format.space_before = Pt(10); h.paragraph_format.space_after = Pt(2)
    return h

def add_para(text, size=10.5, bold=False, italic=False, space_after=4):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.size = Pt(size); r.bold = bold; r.italic = italic
    p.paragraph_format.space_after = Pt(space_after)
    return p

def add_bullet(text, size=10.5):
    p = doc.add_paragraph(style='List Bullet')
    r = p.runs[0] if p.runs else p.add_run('')
    r.text = ''
    r2 = p.add_run(text); r2.font.size = Pt(size)
    p.paragraph_format.space_after = Pt(2)
    return p

def shade(cell, fill):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto'); shd.set(qn('w:fill'), fill)
    tcPr.append(shd)

def add_table(headers, rows, widths=None):
    t = doc.add_table(rows=1+len(rows), cols=len(headers))
    t.style = 'Light Grid Accent 1'
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ''
        p = c.paragraphs[0]
        r = p.add_run(h); r.bold = True; r.font.size = Pt(10.5); r.font.color.rgb = RGBColor(255,255,255)
        shade(c, '2C5282')
    for ri, row in enumerate(rows, 1):
        for ci, v in enumerate(row):
            c = t.rows[ri].cells[ci]
            c.text = ''
            r = c.paragraphs[0].add_run(str(v)); r.font.size = Pt(10)
    if widths:
        for ri in range(len(t.rows)):
            for ci, w in enumerate(widths):
                t.rows[ri].cells[ci].width = Inches(w)
    return t

# ── TITLE ───────────────────────────────────────────────────────────────────
title = doc.add_paragraph()
tr = title.add_run('QR Code Scan Performance')
tr.bold = True; tr.font.size = Pt(20); tr.font.color.rgb = RGBColor.from_string('1F4E79')
title.paragraph_format.space_after = Pt(0)

sub = doc.add_paragraph()
sr = sub.add_run('January 21 – May 28, 2026   |   172 customer scans   |   Prepacks (codeid=4)')
sr.font.size = Pt(10.5); sr.italic = True; sr.font.color.rgb = RGBColor.from_string('666666')
sub.paragraph_format.space_after = Pt(12)

# ── OVERVIEW ────────────────────────────────────────────────────────────────
add_heading('Overview', 1)
add_para(
    "Prepacks have carried QR codes on their packaging since the start of 2026. Customers scan the code with "
    "a phone camera and land directly on the part's McMaster.com product page — no search, no navigation. "
    "This report covers the first four months of that traffic and shows who is scanning, what they look at, "
    "and which products are pulling repeat scans."
)
add_para(
    "Two findings stand out. First, volume is climbing — weekly scans grew roughly 5× between February and "
    "May, with the largest single week (27 scans) occurring May 18. Second, the customers we can identify "
    "skew toward small fabrication shops and credit-card buyers. We can also cleanly attribute about half "
    "of all scans to a known customer account through IP and visitor-ID triangulation."
)

# ── BACKGROUND ──────────────────────────────────────────────────────────────
add_heading('Background', 1)
add_para(
    "Each QR code on a Prepack encodes a McMaster.com URL with two parameters: a part number in the path and "
    "a query string identifying the code type. Prepack codes use codeid=4 (e.g. mcmaster.com/91251A242/?mode=qr&codeid=4). "
    "When scanned, the customer is taken straight to that part's product page. There is no intermediate landing "
    "screen and no login required."
)
add_para(
    "Codeid=4 is reserved for Prepack packaging. Other codeid values exist for separate programs (codeid=2 covers "
    "the assortment kits, for example), and those are not included here."
)

# ── METHODOLOGY ─────────────────────────────────────────────────────────────
add_heading('Methodology', 1)
add_para(
    "We pulled every recorded visit where the landing URL contained mode=qr and codeid=4 between January 21 "
    "and May 28, 2026, using the DigitalAnalytics data warehouse (search_source and visit_source tables) and "
    "the Neo4j interactions graph for event-level detail."
)
add_para(
    "Two filtering passes were applied before analysis:"
)
add_bullet("Internal McMaster-Carr traffic was removed by stripping known internal IP ranges and test devices, "
           "leaving only legitimate customer scans.")
add_bullet("Duplicate visits and visits with no recorded events were de-duplicated against the visit_id key.")
add_para("After cleaning, 172 unique customer scans remained.")

# ── WEEKLY CHART ────────────────────────────────────────────────────────────
add_heading('Volume Trend', 1)
add_para(
    "Scan volume grew steadily through the spring. Single-digit weeks in January and February gave way to "
    "double-digit weeks starting late March, with the strongest period in May."
)
doc.add_picture('/home/user/scheduling/qr_weekly.png', width=Inches(6.7))

# ── CUSTOMER IDENTIFICATION ─────────────────────────────────────────────────
add_heading('Customer Identification', 1)
add_para(
    "QR scans land on a public URL, so we don't get a logged-in customer ID by default. To identify who is "
    "scanning, we triangulate across three signals available at the moment of the scan:"
)
add_bullet("Visitor ID — McMaster's persistent web cookie, present on most modern browser sessions.")
add_bullet("Browse ID — a session-level identifier that can be matched against prior contact activity.")
add_bullet("Client IP address — when the IP matches a known CMF (e.g., a shop with a static business IP), "
           "we can attribute the scan to that account.")
add_para(
    "Across the 172 scans, 90 (52%) triangulated to at least one known customer. The other 82 were either "
    "first-time mobile visitors with no prior account activity, or arrived from residential carrier IPs that "
    "could not be tied to an account.")

# ── ENGAGEMENT TABLE ────────────────────────────────────────────────────────
add_heading('What the Visits Look Like', 1)
add_para(
    "Most scans are short. About 69% of customers landed on the product page and left without further "
    "interaction — typical behavior for QR codes in physical environments, where curious or accidental scans "
    "are common. The remaining 31% explored the site further."
)
add_table(
    ['Engagement', 'Visits', '% of total'],
    [
        ['1 action — landing only',  '119', '69.2%'],
        ['2 to 5 actions',            '41', '23.8%'],
        ['6 to 20 actions',           '12',  '7.0%'],
        ['Total',                    '172', '100.0%'],
    ],
    widths=[2.5, 1.1, 1.5],
)

add_para('', space_after=2)
add_para(
    "Of the engaged customers, three placed items in their order pad and one downloaded a CAD model. "
    "Engaged sessions consistently showed spec filtering, image expansion, and revisits to the scanned "
    "part — behavior consistent with active purchase consideration rather than browsing.",
    space_after=6,
)

add_heading('Devices', 2)
add_para(
    "Mobile phones dominated, as expected. 92% of scans came from a phone (iOS 58%, Android 36%). The "
    "remaining 8% came from desktop browsers — typically a person scanning into a phone, then completing "
    "the visit on their workstation.",
)

# ── PARTS ────────────────────────────────────────────────────────────────────
add_heading('Parts and Repeat Scans', 1)
add_para(
    "Customers scanned 127 distinct part numbers. Most parts (98 of 127, or 77%) were scanned only once — "
    "the long tail you would expect from a broad Prepack catalog. The 29 parts scanned more than once are "
    "the most likely candidates for repeat shop-floor use."
)
add_table(
    ['Part Number', 'Scans'],
    [
        ['91251A242', '5'],
        ['95105A159', '5'],
        ['7073K332',  '4'],
        ['1095K11',   '3'],
        ['91247A628', '3'],
        ['92865A546', '3'],
        ['97467A117', '3'],
        ['92865A543', '3'],
        ['97802A316', '3'],
        ['91400A196', '3'],
        ['91000A469', '3'],
    ],
    widths=[2.0, 1.0],
)
add_para('', space_after=2)
add_para(
    "Parts with three or more scans suggest the QR code is sitting somewhere it gets used regularly — a "
    "shelf label, a maintenance bin, or a tool crib. These are the cleanest signals that the Prepack QR "
    "program is being used as intended.",
)

# ── KEY FINDINGS ────────────────────────────────────────────────────────────
add_heading('Key Findings', 1)
add_bullet("Volume is growing. Weekly scans climbed roughly 5× between February and May. The trend is "
           "consistent enough that we should expect continued growth into Q3 as more Prepacks ship.")
add_bullet("Most scans don't lead to immediate action, but that's normal. The 69% landing-only rate "
           "matches benchmarks for physical QR codes. The 31% engagement rate among the rest is healthy "
           "and includes real purchase signals.")
add_bullet("We can identify the customer behind about half of all scans. The remaining half are mobile "
           "visitors with no prior account history — a growing audience for future engagement.")
add_bullet("Repeat-scan parts point at where the codes are working. The 29 parts scanned more than once "
           "indicate physical placement that's getting reused — shop floors, maintenance areas, or known "
           "reorder points.")
add_bullet("Mobile-first design is essential. 92% of scans came from a phone. Any follow-up actions we "
           "want customers to take from a QR landing page need to work cleanly on a small screen.")

# ── APPENDIX ────────────────────────────────────────────────────────────────
add_heading('Appendix: Definitions', 1)
add_para('Visit', bold=True, size=10.5, space_after=1)
add_para('A continuous browser session ending after 4 hours of inactivity, scoped to a single visit_id.',
         size=10, space_after=4)
add_para('Engagement (user_action_engagement_count)', bold=True, size=10.5, space_after=1)
add_para('The number of deliberate user actions taken during a visit. Excludes passive events like page '
         'scrolls or banner impressions.', size=10, space_after=4)
add_para('Triangulation', bold=True, size=10.5, space_after=1)
add_para('Inferring the customer behind an anonymous scan by combining browser cookie (visitor_id), session '
         'identifier (browse_id), and client IP against known CMF records.', size=10, space_after=4)
add_para('Prepack', bold=True, size=10.5, space_after=1)
add_para('A pre-packaged kit of one or more parts shipped as a single unit, carrying a QR code on its '
         'packaging to make reordering easy.', size=10, space_after=4)

doc.save(OUT)
print(f"Saved → {OUT}")
