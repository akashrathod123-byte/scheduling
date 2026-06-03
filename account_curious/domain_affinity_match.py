#!/usr/bin/env python3
"""
Method 1 — Domain -> CMF affinity matcher.

Question this answers:
    "What % of the logged-in-but-unlinked users can we confidently map to a CMF
     because OTHER people at the same company (same email domain) ARE already
     linked to a CMF?"

How it works:
    1. Read the "with contacts" workbook (everyone with a login + email) and the
       "no CMF" workbook (the unlinked set).
    2. Query the warehouse once for every visitor_id to get its CMF id (if any):
           visitor_id -> contact_visitor_source -> contact_id -> contact_cmf_source -> cmf_id
    3. For each corporate email domain, tally which CMF ids the LINKED people map
       to -> domain -> {cmf_id: count}.
    4. For each UNLINKED person, look at their domain's CMF distribution and score:
           HIGH     - domain maps to exactly one CMF  -> suggest it
           MEDIUM   - one CMF is dominant (>= --dominant share)  -> suggest it
           AMBIGUOUS- domain maps to several CMFs, none dominant
           NONE     - no linked person at this domain (nothing to match to)
       Consumer/free-mail domains (gmail, yahoo, qq...) are reported separately.

Output:
    - console summary: % of unlinked corporate users that are HIGH/MEDIUM matchable
    - <out>: per-person CSV with suggested_cmf_id and match_confidence

SPYDER USERS: edit CONFIG, press Run (F5).
Requires:  pip install pyodbc openpyxl
"""

import csv
import sys
from collections import defaultdict, Counter

import openpyxl
import pyodbc


# ===========================================================================
# EDIT THIS, THEN PRESS RUN (F5).
# ===========================================================================
CONFIG = {
    "with_contacts_xlsx": r"P:\Capacity Management\Management\Akash\B2B\User Models\Account Curious\visitor_with_contacts_email_link.xlsx",
    "no_cmf_xlsx":        r"P:\Capacity Management\Management\Akash\B2B\User Models\Account Curious\test.xlsx",
    "out_csv":            r"P:\Capacity Management\Management\Akash\B2B\User Models\Account Curious\domain_match_results.csv",

    "server":   r"sqlipmds\sqlipmds",
    "database": "DigitalAnalytics",
    "driver":   "ODBC Driver 17 for SQL Server",

    "batch_size": 1000,
    "dominant": 0.80,   # share one CMF must hold to be a MEDIUM-confidence match
}
# ===========================================================================


CONSUMER_DOMAINS = {
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com",
    "msn.com", "icloud.com", "me.com", "mac.com", "yahoo.com", "yahoo.co.uk",
    "yahoo.co.in", "ymail.com", "rocketmail.com", "aol.com", "aim.com",
    "comcast.net", "verizon.net", "att.net", "sbcglobal.net", "bellsouth.net",
    "cox.net", "charter.net", "earthlink.net", "frontier.com", "roadrunner.com",
    "rr.com", "optonline.net", "shaw.ca", "rogers.com", "sympatico.ca",
    "btinternet.com", "sky.com", "orange.fr", "free.fr", "t-online.de",
    "web.de", "gmx.de", "gmx.com", "libero.it", "terra.com", "uol.com.br",
    "protonmail.com", "proton.me", "zoho.com", "fastmail.com", "mail.com",
    "yandex.com", "yandex.ru", "mail.ru", "qq.com", "163.com", "126.com",
    "sina.com", "sohu.com", "foxmail.com", "naver.com", "hanmail.net",
    "daum.net", "nate.com", "rediffmail.com", "mozmail.com",
}
MULTI_LABEL_SUFFIXES = {
    "co.uk", "org.uk", "gov.uk", "ac.uk", "com.au", "net.au", "org.au",
    "edu.au", "gov.au", "co.nz", "co.jp", "or.jp", "ne.jp", "co.kr",
    "com.cn", "net.cn", "org.cn", "com.hk", "com.tw", "com.sg", "com.br",
    "com.mx", "co.in", "co.za", "com.tr", "co.il", "com.sa", "com.my",
    "co.th", "com.ph", "com.vn", "com.co",
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


def read_visitors(path):
    """Return list of (visitor_id:int, registered_domain, is_consumer)."""
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb.active
    out = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            continue
        vid = row[0]
        if isinstance(vid, str) and vid.strip().isdigit():
            vid = int(vid)
        if not isinstance(vid, int):
            continue
        raw = domain_from_email(row[1] if len(row) > 1 else "")
        comp = registered_domain(raw)
        is_consumer = raw in CONSUMER_DOMAINS or comp in CONSUMER_DOMAINS
        out.append((vid, comp, is_consumer))
    wb.close()
    return out


def fetch_cmf_ids(cur, visitor_ids):
    """visitor_id -> cmf_id  (only for visitors linked to a CMF)."""
    result = {}
    ids = list(visitor_ids)
    n = CONFIG["batch_size"]
    for i in range(0, len(ids), n):
        chunk = ids[i:i + n]
        ph = ",".join("?" * len(chunk))
        sql = f"""
            SELECT DISTINCT cv.visitor_id, cc.cmf_id
            FROM        contact_visitor_source AS cv
            JOIN        contact_cmf_source     AS cc ON cc.contact_id = cv.contact_id
            WHERE       cv.visitor_id IN ({ph}) AND cc.cmf_id IS NOT NULL
        """
        cur.execute(sql, chunk)
        for vid, cmf in cur.fetchall():
            # if a visitor maps to >1 cmf just keep the first; rare
            result.setdefault(int(vid), cmf)
        print(f"  queried {min(i + n, len(ids)):,}/{len(ids):,}", end="\r")
    print()
    return result


def main():
    print("Reading workbooks...")
    with_contacts = read_visitors(CONFIG["with_contacts_xlsx"])
    no_cmf = read_visitors(CONFIG["no_cmf_xlsx"])
    print(f"  with_contacts: {len(with_contacts):,} rows | no_cmf: {len(no_cmf):,} rows")

    all_ids = {v for v, _, _ in with_contacts} | {v for v, _, _ in no_cmf}
    print(f"Querying CMF ids for {len(all_ids):,} distinct visitors...")
    conn = connect = pyodbc.connect(
        f"DRIVER={{{CONFIG['driver']}}};SERVER={CONFIG['server']};"
        f"DATABASE={CONFIG['database']};Trusted_Connection=yes;")
    cur = conn.cursor()
    cmf_of = fetch_cmf_ids(cur, all_ids)
    conn.close()

    # domain -> Counter(cmf_id) from everyone who IS linked
    domain_cmf = defaultdict(Counter)
    for vid, comp, is_consumer in with_contacts:
        if is_consumer or not comp:
            continue
        cmf = cmf_of.get(vid)
        if cmf is not None:
            domain_cmf[comp][cmf] += 1

    # score the unlinked corporate people
    buckets = Counter()
    rows_out = []
    for vid, comp, is_consumer in no_cmf:
        if cmf_of.get(vid) is not None:
            buckets["already_linked (false positive)"] += 1
            conf, suggested = "ALREADY LINKED", cmf_of[vid]
        elif is_consumer:
            buckets["consumer email (not domain-matchable)"] += 1
            conf, suggested = "CONSUMER", ""
        else:
            counter = domain_cmf.get(comp)
            if not counter:
                buckets["NONE - no linked peer at domain"] += 1
                conf, suggested = "NONE", ""
            elif len(counter) == 1:
                buckets["HIGH - single CMF at domain"] += 1
                conf, suggested = "HIGH", counter.most_common(1)[0][0]
            else:
                top_cmf, top_n = counter.most_common(1)[0]
                share = top_n / sum(counter.values())
                if share >= CONFIG["dominant"]:
                    buckets["MEDIUM - dominant CMF at domain"] += 1
                    conf, suggested = "MEDIUM", top_cmf
                else:
                    buckets["AMBIGUOUS - multi-CMF domain"] += 1
                    conf, suggested = "AMBIGUOUS", ""
        rows_out.append([vid, comp, conf, suggested])

    with open(CONFIG["out_csv"], "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["visitor_id", "company_domain", "match_confidence",
                    "suggested_cmf_id"])
        w.writerows(rows_out)

    # ---- summary ----
    total = len(no_cmf)
    corp = sum(1 for _, _, c in no_cmf if not c)
    matchable = (buckets["HIGH - single CMF at domain"] +
                 buckets["MEDIUM - dominant CMF at domain"])
    print("\n=== Method 1: domain -> CMF affinity ===")
    print(f"Unlinked visitors analysed: {total:,}")
    for label, n in buckets.most_common():
        print(f"  {n:>8,}  {n/total*100:5.1f}%  {label}")
    print("-" * 50)
    print(f"MATCHABLE (HIGH+MEDIUM): {matchable:,} "
          f"= {matchable/total*100:.1f}% of all unlinked, "
          f"{matchable/corp*100:.1f}% of corporate unlinked")
    print(f"\nPer-person results written to: {CONFIG['out_csv']}")


if __name__ == "__main__":
    main()
