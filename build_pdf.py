"""Generate SLV sprint analysis PDF."""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT

OUT = "/home/user/scheduling/slv_sprint_analysis.pdf"

styles = getSampleStyleSheet()
h1 = ParagraphStyle('h1', parent=styles['Heading1'], fontSize=18,
                    spaceAfter=10, textColor=colors.HexColor('#1a1a1a'))
h2 = ParagraphStyle('h2', parent=styles['Heading2'], fontSize=13,
                    spaceBefore=14, spaceAfter=6, textColor=colors.HexColor('#2c3e50'))
h3 = ParagraphStyle('h3', parent=styles['Heading3'], fontSize=11,
                    spaceBefore=10, spaceAfter=4, textColor=colors.HexColor('#34495e'))
body = ParagraphStyle('body', parent=styles['BodyText'], fontSize=9.5,
                      leading=13, spaceAfter=4)
bullet = ParagraphStyle('bullet', parent=body, leftIndent=14, bulletIndent=2,
                        spaceAfter=3)
caption = ParagraphStyle('caption', parent=body, fontSize=8.5,
                         textColor=colors.HexColor('#666'), spaceAfter=4)
methbox = ParagraphStyle('methbox', parent=body, fontSize=9, leading=12,
                         backColor=colors.HexColor('#f4f6f8'),
                         borderColor=colors.HexColor('#d0d7de'),
                         borderWidth=0.5, borderPadding=8,
                         spaceAfter=10)

def make_table(header, rows, col_widths=None, highlight_last=False):
    data = [header] + rows
    t = Table(data, colWidths=col_widths, hAlign='LEFT')
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8eef3')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a1a1a')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#d0d7de')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fafbfc')]),
    ]
    if highlight_last:
        style += [
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#eef4ec')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]
    t.setStyle(TableStyle(style))
    return t

def bullets(items):
    return [Paragraph(f"• {x}", bullet) for x in items]

doc = SimpleDocTemplate(OUT, pagesize=letter,
                        leftMargin=0.6*inch, rightMargin=0.6*inch,
                        topMargin=0.55*inch, bottomMargin=0.55*inch)

story = []

# ---------- TITLE ----------
story.append(Paragraph("Shipping Location View — Sprint Analysis", h1))
story.append(Paragraph("Eligibility, order volume, manual enrollment, and rule prohibitiveness", caption))
story.append(Spacer(1, 6))

# ---------- METHODOLOGY ----------
story.append(Paragraph("<b>Methodology</b> (applies to all sections)", body))
meth = (
    "• Time window: 12 months, 3/12/2025 → 3/12/2026<br/>"
    "• Excludes 3 shared credit card CMFs (130387900, 12121200, 144173500)<br/>"
    "• &quot;Orders&quot; = contact-attributable orders (~19.5M annually). Orders without contact "
    "attribution can't get SLV regardless of rules, so they're outside scope<br/>"
    "• Earlier 40.8M order figure was inflated by a contact→CMF join bug in "
    "<i>cmf_order_volume.total_orders</i>; corrected to ship-to-based 19.5M"
)
story.append(Paragraph(meth, methbox))

# ============================================================
# SECTION 1 — CMF ELIGIBILITY
# ============================================================
story.append(Paragraph("1. CMF Eligibility", h2))

story.append(Paragraph("Table 1.1: Eligibility (Rules 1 &amp; 3 applied at CMF level)", h3))
story.append(make_table(
    ["", "CMFs", "%"],
    [["Eligible", "1,026,627", "89.6%"],
     ["Non-eligible", "118,842", "10.4%"],
     ["Total active CMFs", "1,145,469", "100%"]],
    col_widths=[3.4*inch, 1.6*inch, 1.0*inch], highlight_last=True))
story.append(Spacer(1, 8))

story.append(Paragraph("Table 1.2: Why CMFs fail", h3))
story.append(make_table(
    ["Reason", "CMFs", "% of failures"],
    [["Rule 3 only — excluded list code (gov/college/distributor)", "105,763", "89.0%"],
     ["Rule 1 only — ≥10 contacts ordered in last 12mo", "11,633", "9.8%"],
     ["Both rules", "1,446", "1.2%"]],
    col_widths=[4.0*inch, 1.2*inch, 1.2*inch]))
story.append(Spacer(1, 8))

story.append(Paragraph("Table 1.3: Ordering activity at active CMFs", h3))
story.append(make_table(
    ["Contacts who ordered in 12mo", "CMFs", "%"],
    [["0", "570,380", "49.8%"],
     ["1", "366,029", "32.0%"],
     ["2–4", "161,991", "14.1%"],
     ["5–9 (still eligible under R1)", "~33,983", "3.0%"],
     ["≥10 (fails R1)", "13,086", "1.1%"]],
    col_widths=[3.4*inch, 1.6*inch, 1.0*inch]))
story.append(Spacer(1, 6))

story.extend(bullets([
    "<b>89.6% of CMFs pass the CMF-level rules</b>, but ~82% of those have 0 or 1 ordering "
    "contact — technically eligible, but SLV has no coworkers to share with.",
    "The &quot;real&quot; SLV-relevant pool is the <b>~17% of CMFs with 2–9 ordering "
    "contacts (~196K CMFs)</b> — that's where shared view actually does something.",
]))

# ============================================================
# SECTION 2 — ORDER ELIGIBILITY
# ============================================================
story.append(PageBreak())
story.append(Paragraph("2. Order Eligibility (Corrected)", h2))

story.append(Paragraph("Table 2.1: Orders by CMF eligibility", h3))
story.append(make_table(
    ["", "Orders", "%"],
    [["At eligible CMFs", "14,675,817", "75.3%"],
     ["At non-eligible CMFs", "4,809,497", "24.7%"],
     ["Total orders", "19,485,314", "100%"]],
    col_widths=[3.4*inch, 1.6*inch, 1.0*inch], highlight_last=True))
story.append(Spacer(1, 8))

story.append(Paragraph("Table 2.2: CMFs vs. orders — the disparity", h3))
story.append(make_table(
    ["Segment", "% of CMFs", "% of orders", "Order/CMF ratio"],
    [["Eligible", "89.6%", "75.3%", "0.84x"],
     ["Non-eligible", "10.4%", "24.7%", "2.4x"]],
    col_widths=[2.4*inch, 1.4*inch, 1.4*inch, 1.4*inch]))
story.append(Spacer(1, 8))

story.append(Paragraph("Table 2.3: High-activity CMFs (≥10 contacts — fail Rule 1)", h3))
story.append(make_table(
    ["", "CMFs", "Orders", "Avg orders/CMF"],
    [["High-activity", "12,984", "4,075,186", "314"],
     ["% of total", "1.1%", "20.9%", "—"]],
    col_widths=[2.4*inch, 1.4*inch, 1.4*inch, 1.4*inch]))
story.append(Spacer(1, 6))

story.extend(bullets([
    "<b>Big customers are disproportionately shut out:</b> 10.4% of CMFs account for 24.7% of "
    "orders — a 2.4x over-index.",
    "<b>Rule 1 alone shuts out 20.9% of all orders</b> from just 1.1% of CMFs — the headline exclusion.",
]))

# ============================================================
# SECTION 3 — MANUAL ENROLLMENT
# ============================================================
story.append(Spacer(1, 14))
story.append(Paragraph("3. Manual SLV Enrollment", h2))

story.append(Paragraph("Table 3.1: How contacts got SLV", h3))
story.append(make_table(
    ["", "Contacts", "%"],
    [["Any manual enrollment", "15,481", "3.28%"],
     ["    Manual-only (no algo records)", "10,680", "2.26%"],
     ["    Both manual + algo", "4,801", "1.02%"],
     ["Algorithm-only", "456,369", "96.72%"],
     ["Total SLV-enrolled contacts", "471,850", "100%"]],
    col_widths=[3.4*inch, 1.6*inch, 1.0*inch], highlight_last=True))
story.append(Spacer(1, 6))

story.extend(bullets([
    "<b>~97% of SLV came from the algorithm</b>; ~3% from Sales manually flipping the toggle on webmaster/.",
    "<b>~10.7K contacts (2.3%) are &quot;true overrides&quot;</b> — Sales added them; the algorithm "
    "never qualified them. That's the cleanest measure of how often the auto-rules aren't enough.",
]))

# ============================================================
# SECTION 4 — RULE PROHIBITIVENESS
# ============================================================
story.append(PageBreak())
story.append(Paragraph("4. Rule-by-Rule Prohibitiveness", h2))
story.append(Paragraph("All 4 rules measured against the same 19.5M contact-attributable order denominator.", caption))

story.append(Paragraph("Table 4.1: Ranked by orders excluded", h3))
story.append(make_table(
    ["Rank", "Rule", "What it does", "Orders excluded", "% of orders"],
    [["1", "R1", "<10 active contacts at ship-to", "4,075,186", "20.9%"],
     ["2", "R4", "Single non-individual billto", "1,862,848", "9.6%"],
     ["3", "R3", "Listcode not gov/college/distributor", "1,155,818", "5.9%"],
     ["4", "R2", "≥3 orders this ship-to", "835,286", "4.3%"]],
    col_widths=[0.5*inch, 0.5*inch, 2.7*inch, 1.5*inch, 1.0*inch]))
story.append(Spacer(1, 8))

story.append(Paragraph("Table 4.2: Ranked by entities failing", h3))
story.append(make_table(
    ["Rank", "Rule", "Pairs failing", "% of pairs", "Contacts shut out", "CMFs"],
    [["1", "R2", "644,137", "46.8%", "611,259", "250,798"],
     ["2", "R1", "264,974", "19.2%", "248,827", "12,984"],
     ["3", "R3", "113,008", "8.2%", "103,156", "43,901"],
     ["4", "R4", "95,569", "6.9%", "43,487", "66,179"]],
    col_widths=[0.5*inch, 0.5*inch, 1.1*inch, 0.9*inch, 1.3*inch, 1.0*inch]))
story.append(Spacer(1, 8))

story.append(Paragraph("Table 4.3: R2 caller-name proxy (orders <3 in 12mo)", h3))
story.append(make_table(
    ["Caller names with…", "Count", "% of 1,386,228"],
    [["1 total order in 12mo", "506,925", "36.6%"],
     ["2 total orders in 12mo", "185,179", "13.4%"],
     ["<3 total orders in 12mo", "692,104", "49.9%"]],
    col_widths=[3.4*inch, 1.6*inch, 1.4*inch], highlight_last=True))
story.append(Spacer(1, 6))

story.append(Paragraph("<b>Methodology</b>", h3))
story.extend(bullets([
    "R1 &amp; R3 are CMF-level rules; R2 is contact-ship-to level; R4 is contact level. All converted to orders for apples-to-apples comparison.",
    "&quot;Orders excluded&quot; = orders this rule alone would block, assuming no other rules apply. Rules are not mutually exclusive — overlap exists.",
    "R2 measured two ways: strict (pairs with &lt;3 orders to that ship-to) and proxy (caller names with &lt;3 orders total).",
]))

story.append(Paragraph("<b>Takeaways</b>", h3))
story.extend(bullets([
    "<b>R1 is the volume killer.</b> 1% of CMFs fail it, but they cover 21% of all orders — the big-customer exclusion is doing most of the work.",
    "<b>R2 is the headcount killer.</b> 47% of contact-ship-to pairs fail it, and <b>half of all caller names (49.9%) have &lt;3 total orders in a year</b> — they can't qualify under R2 at <i>any</i> ship-to. R2 has the biggest &quot;shut out but still visit the web&quot; footprint.",
    "<b>R4 punches above its weight.</b> 7% of pairs fail it but 10% of orders excluded — multi-billto contacts are heavy orderers (~3× density).",
    "<b>R3 (listcode) is the smallest on both axes.</b> Real, but not the headline.",
]))

doc.build(story)
print(f"Wrote {OUT}")
