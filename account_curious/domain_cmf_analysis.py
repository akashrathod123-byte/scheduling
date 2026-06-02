#!/usr/bin/env python3
"""
Account Curious — Domain / CMF coverage analysis
================================================

Goal
----
Take the visitor email exports and roll them up *by company* (using the email
domain) so we can answer questions like:

    "spacex has 87 emails and 23 of them are NOT linked to the CMF"

Inputs (see the B2B / User Models / Account Curious folder)
-----------------------------------------------------------
1. visitor_with_contacts_email_link.csv  (the "denominator")
       Everyone we know who has logged in over the trailing window, i.e. every
       visitor that has a contact + an email.  This is the TOTAL pool of
       emails/logins at each company.

2. visitor_no_cmf_email_link.csv         (the "not linked" set)
       Visitors that have a contact_id but are NOT linked to a CMF (Customer
       Master File).  Per the data-warehouse model, a CMF is the company
       account record; contacts connect to CMFs via contact_cmf_source.  These
       are the people we have *not* tied to a company account yet.

For each file the relevant columns are a Visitor ID and an Email.  The company
is derived from the email domain (e.g. jane@fastenal.com -> fastenal.com), with
sub-domains rolled up to the registered domain (stores.fastenal.com -> the
Fastenal bucket, its.jnj.com -> the J&J bucket).

Free/consumer mail providers (gmail, yahoo, qq.com, ...) are NOT companies, so
they are excluded from the company report by default (use --include-consumer to
keep them, or see the *_consumer.csv side output).

Output
------
A CSV (and an on-screen summary) with one row per company:

    company_domain, total_emails, linked_to_cmf, not_linked_to_cmf,
    pct_not_linked, total_login_records, not_linked_login_records

"total_emails" / "not_linked_to_cmf" are counts of DISTINCT visitor IDs (people)
which matches the "Count of Visitor ID" pivot in the source workbooks.  The
"*_login_records" columns are the raw row counts (a visitor can appear under
more than one email) for transparency.

If only the no_cmf file is supplied, the report still lists every company with
its "not linked" count — the total/linked columns are just left blank because
the denominator file wasn't provided.

Usage
-----
    python3 domain_cmf_analysis.py \
        --no-cmf        visitor_no_cmf_email_link.csv \
        --with-contacts visitor_with_contacts_email_link.csv \
        --out           company_cmf_coverage.csv

    # only the file we have today:
    python3 domain_cmf_analysis.py --no-cmf visitor_no_cmf_email_link.csv

Pure standard library — no pip installs required.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import defaultdict


# ===========================================================================
# EASY MODE (Spyder / "just press Run") — edit these paths, then run the file.
# These are only used when you run with NO command-line arguments (e.g. via
# %runfile in the Spyder/IPython console).  If you pass --no-cmf on the command
# line, these are ignored.
# ===========================================================================
CONFIG = {
    # Required: the not-linked-to-CMF export.
    "no_cmf":        r"P:\Capacity Management\Management\Akash\B2B\User Models\Account Curious\visitor_no_cmf_email_link.csv",
    # Optional: the total pool. Leave as "" if you only have the no_cmf file.
    "with_contacts": r"P:\Capacity Management\Management\Akash\B2B\User Models\Account Curious\visitor_with_contacts_email_link.csv",
    # Where to write the result.
    "out":           r"P:\Capacity Management\Management\Akash\B2B\User Models\Account Curious\company_cmf_coverage.csv",
    "top": 30,
    "min_emails": 1,
    "sort_by": "not_linked",   # "not_linked" | "total" | "pct"
    "include_consumer": False,
}


# ---------------------------------------------------------------------------
# Consumer / free email providers.  These are mailbox providers, NOT companies,
# so we don't want them showing up as "companies" in the report.  Extend freely.
# ---------------------------------------------------------------------------
CONSUMER_DOMAINS = {
    # Google / Microsoft / Apple / Yahoo / AOL
    "gmail.com", "googlemail.com",
    "outlook.com", "hotmail.com", "live.com", "msn.com", "passport.com",
    "outlook.com.br", "hotmail.co.uk", "hotmail.fr", "live.co.uk",
    "icloud.com", "me.com", "mac.com",
    "yahoo.com", "yahoo.co.uk", "yahoo.co.in", "yahoo.fr", "yahoo.es",
    "yahoo.de", "yahoo.ca", "ymail.com", "rocketmail.com",
    "aol.com", "aim.com",
    # ISP / telco mailboxes
    "comcast.net", "verizon.net", "att.net", "sbcglobal.net", "bellsouth.net",
    "cox.net", "charter.net", "earthlink.net", "frontier.com", "windstream.net",
    "roadrunner.com", "rr.com", "optonline.net", "juno.com", "netzero.net",
    "shaw.ca", "rogers.com", "sympatico.ca", "telus.net", "bell.net",
    "btinternet.com", "sky.com", "virginmedia.com", "ntlworld.com",
    "orange.fr", "free.fr", "wanadoo.fr", "laposte.net", "sfr.fr",
    "t-online.de", "web.de", "gmx.de", "gmx.com", "gmx.net", "freenet.de",
    "libero.it", "virgilio.it", "alice.it", "tin.it",
    "terra.com", "uol.com.br", "bol.com.br", "ig.com.br", "globo.com",
    # privacy / generic webmail
    "protonmail.com", "proton.me", "pm.me", "tutanota.com", "tuta.io",
    "zoho.com", "zohomail.com", "fastmail.com", "hushmail.com",
    "mail.com", "email.com", "usa.com", "consultant.com", "gmx.us",
    "yandex.com", "yandex.ru", "mail.ru", "inbox.ru", "list.ru", "bk.ru",
    "rambler.ru",
    # China / Asia consumer mail
    "qq.com", "163.com", "126.com", "yeah.net", "sina.com", "sina.cn",
    "sohu.com", "aliyun.com", "foxmail.com", "vip.163.com", "vip.qq.com",
    "naver.com", "hanmail.net", "daum.net", "nate.com",
    "rediffmail.com", "rediff.com",
    # disposable / junk
    "mailinator.com", "guerrillamail.com", "10minutemail.com", "trashmail.com",
    "temp-mail.org", "yopmail.com", "sharklasers.com", "getnada.com",
    "example.com", "test.com", "domain.com", "none.com", "noemail.com",
}


# ---------------------------------------------------------------------------
# Minimal public-suffix handling so sub-domains roll up to the registered
# (company) domain.  We special-case the common multi-label suffixes; everything
# else is treated as a normal single-label TLD (the last two labels are the
# registered domain).  This avoids a network/pip dependency on tldextract.
# ---------------------------------------------------------------------------
MULTI_LABEL_SUFFIXES = {
    "co.uk", "org.uk", "gov.uk", "ac.uk", "ltd.uk", "plc.uk", "me.uk", "net.uk",
    "com.au", "net.au", "org.au", "edu.au", "gov.au", "id.au",
    "co.nz", "net.nz", "org.nz", "govt.nz", "ac.nz",
    "co.jp", "or.jp", "ne.jp", "go.jp", "ac.jp", "ad.jp", "ed.jp",
    "co.kr", "or.kr", "go.kr", "ne.kr", "re.kr", "ac.kr",
    "com.cn", "net.cn", "org.cn", "gov.cn", "edu.cn", "ac.cn",
    "com.hk", "org.hk", "net.hk", "gov.hk", "edu.hk",
    "com.tw", "org.tw", "net.tw", "gov.tw", "edu.tw",
    "com.sg", "net.sg", "org.sg", "gov.sg", "edu.sg",
    "com.br", "net.br", "org.br", "gov.br", "edu.br",
    "com.mx", "gob.mx", "org.mx", "net.mx", "edu.mx",
    "com.ar", "gob.ar", "org.ar", "net.ar",
    "co.in", "net.in", "org.in", "gov.in", "edu.in", "ac.in", "res.in",
    "co.za", "org.za", "net.za", "gov.za", "ac.za",
    "com.tr", "gov.tr", "org.tr", "net.tr", "edu.tr",
    "co.il", "org.il", "net.il", "gov.il", "ac.il",
    "com.sa", "gov.sa", "org.sa", "net.sa", "edu.sa",
    "com.my", "gov.my", "org.my", "net.my", "edu.my",
    "co.th", "in.th", "go.th", "or.th", "ac.th",
    "com.ph", "gov.ph", "org.ph", "net.ph", "edu.ph",
    "com.vn", "gov.vn", "org.vn", "net.vn", "edu.vn",
    "com.co", "gov.co", "org.co", "net.co", "edu.co",
}


def registered_domain(domain: str) -> str:
    """Roll a host/domain up to its registered (company) domain.

    fastenal.com           -> fastenal.com
    stores.fastenal.com    -> fastenal.com
    its.jnj.com            -> jnj.com
    foo.bar.co.uk          -> bar.co.uk
    """
    domain = domain.strip().lower().rstrip(".")
    if not domain:
        return ""
    labels = domain.split(".")
    if len(labels) <= 2:
        return domain
    last_two = ".".join(labels[-2:])
    last_three = ".".join(labels[-3:])
    if last_two in MULTI_LABEL_SUFFIXES and len(labels) >= 3:
        return last_three
    return last_two


def domain_from_email(email: str) -> str:
    """Pull the domain out of an email address, lower-cased and cleaned."""
    email = (email or "").strip().lower()
    if "@" not in email:
        return ""
    dom = email.rsplit("@", 1)[1].strip().strip(">").strip()
    # guard against stray whitespace / trailing punctuation
    return dom.split()[0].rstrip(".,;") if dom else ""


def _find_columns(header):
    """Locate the Visitor ID and Email columns in a header row.

    Returns (visitor_idx, email_idx).  Falls back to positional defaults
    (col 0 = Visitor ID, col 1 = Email) when names aren't recognised.
    """
    visitor_idx = email_idx = None
    for i, name in enumerate(header):
        key = (name or "").strip().lower()
        if visitor_idx is None and "visitor" in key:
            visitor_idx = i
        if email_idx is None and key == "email":
            email_idx = i
    if email_idx is None:
        # any column containing "email"
        for i, name in enumerate(header):
            if "email" in (name or "").strip().lower():
                email_idx = i
                break
    if visitor_idx is None:
        visitor_idx = 0
    if email_idx is None:
        email_idx = 1
    return visitor_idx, email_idx


def load_file(path, consumer_domains):
    """Read one export.

    Returns a dict keyed by registered company domain:
        domain -> {"visitors": set(visitor_id), "records": int,
                   "is_consumer": bool}
    Rows with no usable email/domain are skipped (counted in `skipped`).
    """
    stats = {
        "rows": 0,
        "skipped_no_email": 0,
        "consumer_rows": 0,
    }
    data = defaultdict(lambda: {"visitors": set(), "records": 0,
                                "is_consumer": False})
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        header = next(reader, [])
        v_idx, e_idx = _find_columns(header)
        for row in reader:
            if not row or v_idx >= len(row):
                continue
            visitor = row[v_idx].strip()
            if not visitor:
                continue
            email = row[e_idx].strip() if e_idx < len(row) else ""
            raw_domain = domain_from_email(email)
            if not raw_domain:
                stats["skipped_no_email"] += 1
                continue
            stats["rows"] += 1
            company = registered_domain(raw_domain)
            is_consumer = (raw_domain in consumer_domains
                           or company in consumer_domains)
            if is_consumer:
                stats["consumer_rows"] += 1
            bucket = data[company]
            bucket["visitors"].add(visitor)
            bucket["records"] += 1
            bucket["is_consumer"] = is_consumer
    return data, stats


def build_report(no_cmf, with_contacts):
    """Merge the two datasets into per-company rows."""
    companies = set(no_cmf) | set(with_contacts)
    rows = []
    for domain in companies:
        nc = no_cmf.get(domain)
        wc = with_contacts.get(domain)
        is_consumer = (nc and nc["is_consumer"]) or (wc and wc["is_consumer"])

        not_linked_visitors = len(nc["visitors"]) if nc else 0
        not_linked_records = nc["records"] if nc else 0

        if wc:
            total_visitors = len(wc["visitors"])
            total_records = wc["records"]
        else:
            # No denominator file: we at least know the not-linked people exist.
            total_visitors = None
            total_records = None

        if total_visitors is not None:
            # not_linked should be a subset of total; clamp just in case the
            # exports are from slightly different snapshots.
            not_linked_visitors = min(not_linked_visitors, total_visitors)
            linked = total_visitors - not_linked_visitors
            pct = (not_linked_visitors / total_visitors * 100.0
                   if total_visitors else 0.0)
        else:
            linked = None
            pct = None

        rows.append({
            "company_domain": domain,
            "is_consumer": is_consumer,
            "total_emails": total_visitors,
            "linked_to_cmf": linked,
            "not_linked_to_cmf": not_linked_visitors,
            "pct_not_linked": pct,
            "total_login_records": total_records,
            "not_linked_login_records": not_linked_records,
        })
    return rows


def write_csv(rows, path):
    fields = ["company_domain", "total_emails", "linked_to_cmf",
              "not_linked_to_cmf", "pct_not_linked", "total_login_records",
              "not_linked_login_records"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(fields)
        for r in rows:
            w.writerow([
                r["company_domain"],
                "" if r["total_emails"] is None else r["total_emails"],
                "" if r["linked_to_cmf"] is None else r["linked_to_cmf"],
                r["not_linked_to_cmf"],
                "" if r["pct_not_linked"] is None
                else f"{r['pct_not_linked']:.1f}",
                "" if r["total_login_records"] is None
                else r["total_login_records"],
                r["not_linked_login_records"],
            ])


def sentence(r):
    """Human-readable one-liner, mirroring the example in the brief."""
    name = r["company_domain"]
    if r["total_emails"] is not None:
        return (f"{name} has {r['total_emails']} emails and "
                f"{r['not_linked_to_cmf']} of them are not linked to the CMF "
                f"({r['pct_not_linked']:.0f}%).")
    return (f"{name} has {r['not_linked_to_cmf']} emails not linked to the CMF "
            f"(total unknown — provide the with-contacts file).")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Roll visitor email exports up by company and report CMF "
                    "coverage (how many emails per company, how many not "
                    "linked to a CMF).")
    ap.add_argument("--no-cmf", required=True,
                    help="visitor_no_cmf_email_link.csv (the not-linked set)")
    ap.add_argument("--with-contacts", default=None,
                    help="visitor_with_contacts_email_link.csv (the total pool)")
    ap.add_argument("--out", default="company_cmf_coverage.csv",
                    help="output CSV path (default: company_cmf_coverage.csv)")
    ap.add_argument("--top", type=int, default=30,
                    help="how many companies to print on screen (default 30)")
    ap.add_argument("--min-emails", type=int, default=1,
                    help="only report companies with at least this many "
                         "not-linked emails (default 1)")
    ap.add_argument("--sort-by", choices=["not_linked", "total", "pct"],
                    default="not_linked",
                    help="ranking for the on-screen summary (default not_linked)")
    ap.add_argument("--include-consumer", action="store_true",
                    help="keep gmail/yahoo/qq etc. in the company report")

    # If no command-line args were given (e.g. run from Spyder via %runfile),
    # fall back to the CONFIG block at the top of this file.
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print("No command-line arguments given — using the CONFIG block at the "
              "top of this file.\n(Edit those paths if they're wrong.)\n")
        args = argparse.Namespace(
            no_cmf=CONFIG["no_cmf"],
            with_contacts=CONFIG["with_contacts"] or None,
            out=CONFIG["out"],
            top=CONFIG["top"],
            min_emails=CONFIG["min_emails"],
            sort_by=CONFIG["sort_by"],
            include_consumer=CONFIG["include_consumer"],
        )
    else:
        args = ap.parse_args(argv)

    consumer = set() if args.include_consumer else CONSUMER_DOMAINS

    if not os.path.exists(args.no_cmf):
        ap.error(f"--no-cmf file not found: {args.no_cmf}")

    no_cmf, nc_stats = load_file(args.no_cmf, consumer)
    print(f"Loaded no_cmf:        {nc_stats['rows']:>8,} rows  "
          f"({nc_stats['consumer_rows']:,} consumer, "
          f"{nc_stats['skipped_no_email']:,} skipped)")

    if args.with_contacts:
        if not os.path.exists(args.with_contacts):
            ap.error(f"--with-contacts file not found: {args.with_contacts}")
        with_contacts, wc_stats = load_file(args.with_contacts, consumer)
        print(f"Loaded with_contacts: {wc_stats['rows']:>8,} rows  "
              f"({wc_stats['consumer_rows']:,} consumer, "
              f"{wc_stats['skipped_no_email']:,} skipped)")
    else:
        with_contacts = {}
        print("NOTE: no --with-contacts file given. Reporting NOT-LINKED "
              "counts per company; 'total emails' will be blank.\n"
              "      Provide visitor_with_contacts_email_link.csv for the "
              "full 'X of Y not linked' picture.")

    rows = build_report(no_cmf, with_contacts)

    # company-only report (drop consumer providers unless asked to keep them)
    company_rows = [r for r in rows if not r["is_consumer"]]
    consumer_rows = [r for r in rows if r["is_consumer"]]

    company_rows = [r for r in company_rows
                    if r["not_linked_to_cmf"] >= args.min_emails]

    def sort_key(r):
        if args.sort_by == "total":
            return (r["total_emails"] or 0, r["not_linked_to_cmf"])
        if args.sort_by == "pct":
            return (r["pct_not_linked"] or 0, r["not_linked_to_cmf"])
        return (r["not_linked_to_cmf"], r["total_emails"] or 0)

    company_rows.sort(key=sort_key, reverse=True)

    write_csv(company_rows, args.out)
    if consumer_rows:
        base, ext = os.path.splitext(args.out)
        consumer_path = f"{base}_consumer{ext or '.csv'}"
        consumer_rows.sort(key=lambda r: r["not_linked_to_cmf"], reverse=True)
        write_csv(consumer_rows, consumer_path)

    # ---- on-screen summary -------------------------------------------------
    total_companies = len(company_rows)
    total_not_linked = sum(r["not_linked_to_cmf"] for r in company_rows)
    print()
    print(f"Identified {total_companies:,} companies "
          f"(consumer/free providers excluded).")
    print(f"Total emails not linked to a CMF at those companies: "
          f"{total_not_linked:,}")
    print(f"Full report written to: {args.out}")
    print()
    print(f"Top {min(args.top, total_companies)} companies "
          f"(by {args.sort_by}):")
    print("-" * 72)
    for r in company_rows[:args.top]:
        print("  " + sentence(r))

    return 0


if __name__ == "__main__":
    sys.exit(main())
