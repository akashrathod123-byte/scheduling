#!/usr/bin/env python3
"""
Add column D = the actual CMF(s) for each company domain in the
"Easy Wins by Company" tab of Connecting Account Curious.xlsx.

How it works:
    1. Read the Easy Wins tab -> the list of company domains we care about.
    2. Read the full logins file (visitor_with_contacts_email_link) and keep
       only the visitors whose email domain is one of those companies.
    3. Look each of those visitors up in the warehouse to get their CMF id
       (visitor -> contact_visitor_source -> contact -> contact_cmf_source -> cmf_id).
    4. For each domain, tally which CMFs its linked people belong to, and write
       the TOP 15 (cmf_id: #people) into a new column D, sorted most-common first.
    5. Save the workbook back (the Summary tab and formatting are preserved).

SPYDER USERS: edit CONFIG, press Run (F5).
Requires:  pip install pyodbc openpyxl
"""

import csv
import os
from collections import defaultdict, Counter

import openpyxl
import pyodbc


# ===========================================================================
# EDIT THIS, THEN PRESS RUN (F5).
# ===========================================================================
CONFIG = {
    "workbook":      r"P:\Capacity Management\Management\Akash\B2B\User Models\Account Curious\Connecting Account Curious.xlsx",
    "sheet":         "Easy Wins by Company",
    "with_contacts": r"P:\Capacity Management\Management\Akash\B2B\User Models\Account Curious\visitor_with_contacts_email_link.csv",

    "server":   r"sqlipmds\sqlipmds",
    "database": "DigitalAnalytics",
    "driver":   "ODBC Driver 17 for SQL Server",

    "top_cmfs":  15,     # how many CMFs to list per domain
    "batch_size": 1000,
}
# ===========================================================================


CONSUMER_DOMAINS = {
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com",
    "msn.com", "icloud.com", "me.com", "mac.com", "yahoo.com", "ymail.com",
    "aol.com", "comcast.net", "verizon.net", "att.net", "sbcglobal.net",
    "cox.net", "charter.net", "qq.com", "163.com", "126.com", "naver.com",
    "mail.ru", "yandex.com", "proton.me", "protonmail.com", "mozmail.com",
}
MULTI_LABEL_SUFFIXES = {
    "co.uk", "org.uk", "gov.uk", "ac.uk", "com.au", "net.au", "org.au",
    "co.nz", "co.jp", "co.kr", "com.cn", "com.hk", "com.tw", "com.sg",
    "com.br", "com.mx", "co.in", "co.za", "com.tr", "co.il",
}


def registered_domain(domain):
    domain = (domain or "").strip().lower().rstrip(".")
    labels = domain.split(".")
    if len(labels) <= 2:
        return domain
    if ".".join(labels[-2:]) in MULTI_LABEL_SUFFIXES:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def domain_from_email(email):
    email = (email or "").strip().lower()
    if "@" not in email:
        return ""
    dom = email.rsplit("@", 1)[1].strip().strip(">").strip()
    return dom.split()[0].rstrip(".,;") if dom else ""


def find_header(ws):
    """Locate the header row and the company-domain column on the sheet."""
    for r in range(1, 12):
        for c in range(1, 8):
            val = ws.cell(r, c).value
            if val and "company" in str(val).lower():
                return r, c
    # fallback: assume header on row 3, domain in col A (matches our workbook)
    return 3, 1


def read_csv_visitors(path, target_domains):
    """Yield (visitor_id:int, registered_domain) for rows whose domain is a
    target. Skips Excel-mangled (scientific-notation) ids and warns."""
    kept = 0
    bad_ids = 0
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        next(reader, None)  # header
        for row in reader:
            if not row or not row[0].strip():
                continue
            comp = registered_domain(domain_from_email(row[1] if len(row) > 1 else ""))
            if comp not in target_domains:
                continue
            vid = row[0].strip()
            if not vid.isdigit():          # e.g. "9.36332E+12" -> precision lost
                bad_ids += 1
                continue
            kept += 1
            yield int(vid), comp
    if bad_ids:
        print(f"  WARNING: skipped {bad_ids:,} visitor IDs that were saved in "
              f"scientific notation (re-export with_contacts as TEXT/xlsx to include them).")
    print(f"  kept {kept:,} linked-candidate rows at target domains")


def fetch_cmf_ids(cur, visitor_ids):
    """visitor_id -> cmf_id (only visitors actually linked to a CMF)."""
    result = {}
    ids = list(visitor_ids)
    n = CONFIG["batch_size"]
    for i in range(0, len(ids), n):
        chunk = ids[i:i + n]
        ph = ",".join("?" * len(chunk))
        sql = f"""
            SELECT DISTINCT cv.visitor_id, cc.cmf_id
            FROM   contact_visitor_source AS cv
            JOIN   contact_cmf_source     AS cc ON cc.contact_id = cv.contact_id
            WHERE  cv.visitor_id IN ({ph}) AND cc.cmf_id IS NOT NULL
        """
        cur.execute(sql, chunk)
        for vid, cmf in cur.fetchall():
            result.setdefault(int(vid), cmf)
        print(f"  queried {min(i + n, len(ids)):,}/{len(ids):,}", end="\r")
    print()
    return result


def main():
    # ---- 1. read the domains from the Easy Wins tab ----
    print("Opening workbook...")
    wb = openpyxl.load_workbook(CONFIG["workbook"])
    ws = wb[CONFIG["sheet"]]
    hdr_row, dom_col = find_header(ws)
    print(f"  header on row {hdr_row}, company domain in column "
          f"{openpyxl.utils.get_column_letter(dom_col)}")

    domain_rows = {}  # domain -> excel row number
    for r in range(hdr_row + 1, ws.max_row + 1):
        d = ws.cell(r, dom_col).value
        if d:
            domain_rows[str(d).strip().lower()] = r
    target_domains = set(domain_rows)
    print(f"  {len(target_domains):,} company domains to resolve")

    # ---- 2. pull the linked-candidate visitors at those domains ----
    print("Reading full logins file (only rows at those domains)...")
    cand = list(read_csv_visitors(CONFIG["with_contacts"], target_domains))
    visitor_domain = {v: d for v, d in cand}

    # ---- 3. warehouse lookup ----
    print(f"Querying warehouse for {len(visitor_domain):,} visitors...")
    conn = pyodbc.connect(
        f"DRIVER={{{CONFIG['driver']}}};SERVER={CONFIG['server']};"
        f"DATABASE={CONFIG['database']};Trusted_Connection=yes;")
    cur = conn.cursor()
    cmf_of = fetch_cmf_ids(cur, visitor_domain.keys())
    conn.close()

    # ---- 4. domain -> Counter(cmf) ----
    domain_cmfs = defaultdict(Counter)
    for vid, cmf in cmf_of.items():
        domain_cmfs[visitor_domain[vid]][cmf] += 1

    # ---- 5. write column D ----
    out_col = 4  # column D
    ws.cell(hdr_row, out_col, f"Top {CONFIG['top_cmfs']} CMF(s)  (cmf_id: #linked people)")
    ws.cell(hdr_row, out_col).font = ws.cell(hdr_row, 1).font  # mimic header style

    resolved = 0
    for d, r in domain_rows.items():
        counter = domain_cmfs.get(d)
        if counter:
            resolved += 1
            top = counter.most_common(CONFIG["top_cmfs"])
            text = " | ".join(f"{cmf}: {n}" for cmf, n in top)
            extra = len(counter) - len(top)
            if extra > 0:
                text += f"  (+{extra} more)"
        else:
            text = "(no linked person found)"
        ws.cell(r, out_col, text)

    # extend the autofilter to include column D if one is set
    if ws.auto_filter.ref:
        ws.auto_filter.ref = ws.auto_filter.ref.replace(
            ":C", ":D").replace(":c", ":D")
    ws.column_dimensions[openpyxl.utils.get_column_letter(out_col)].width = 60

    wb.save(CONFIG["workbook"])
    print(f"\nDone. Resolved CMFs for {resolved:,}/{len(target_domains):,} domains.")
    print(f"Saved: {CONFIG['workbook']}")


if __name__ == "__main__":
    main()
