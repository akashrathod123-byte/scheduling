"""
CWIPS file inspector + parser.

Run this on your machine, pointing at the mainframe-downloaded file:
    python parse_cwips.py "P:\\Capacity Management\\Management\\Akash\\B2B\\cwips_jan2026.TXT"

Stage 1 (inspect): prints first 5 records as hex + ASCII so we can confirm
whether the file is:
  - Plain text (ASCII, lines with newlines)
  - EBCDIC text (no ASCII chars; mainframe untranslated)
  - Fixed-width binary with packed decimals (text fields readable, numerics garbled)

Stage 2 (parse): assumes a fixed-width text export (which is what you'd get
if you downloaded with text-mode FTP / IND$FILE with charset translation on).
If the file is binary, you'll see garbage in the numeric columns and we'll
need a different download or a more involved parser.

CWIPS spec is in Using_the_Customer_Work_in_Process_Data_Files (Aug 2013).
"""

import argparse
import csv
import os
import sys
from collections import Counter, defaultdict

# CWIPS field layout — (name, length).
# Numeric and "Pack" fields are sized assuming an unpacked / text export.
# If you got a binary export, packed fields take ceil((length+1)/2) bytes
# instead and we'd need to switch parsing strategy.
CWIPS_FIELDS = [
    ("EXTRACTDT",        8),
    ("REG",              9),
    ("REGBASE",          7),
    ("REGSUFFIX",        2),
    ("REQUESTID",        7),
    ("REQUESTTYPEDSC",  40),
    ("WORKTYPECD",       8),
    ("WORK",            25),
    ("WAYPOINTIND",      1),
    ("QUEUEDUR",         7),   # 5 digits + 2 decimal
    ("ACTIVEDUR",        7),
    ("WAITDUR",          7),
    ("PROCESSDUR",       7),
    ("BEGINDATE",        8),
    ("BEGINTIME",        6),
    ("BEGINACTOR",       8),
    ("BEGINBRANCH",      2),
    ("ENDDATE",          8),
    ("ENDTIME",          6),
    ("ENDACTOR",         8),
    ("ENDBRANCH",        2),
    ("NUMTOUCHES",       4),
    ("EXCEPTIONIND",     1),
    ("DOCID",           10),
    ("SHIPTON",          5),
    ("BILLTON",          5),
    ("CUSTOMERACCOUNT",  5),
    ("OWNBRANCH",        2),
    ("LISTCODE",         2),
    ("ORDERSTATE",       8),
    ("SOURCEADDRESS",   75),
    ("ASSOCORDERS",      4),
    ("ASSOCREQUESTS",    4),
    ("NONCATALOGIND",    1),
    ("BACKORDERIND",     1),
    ("FILLABLEIND",      1),
    ("LARGEDOLLARIND",   1),
    ("CANCELLEDIND",     1),
    ("CREDITREVIND",     1),
    ("COMPLIANCEIND",    1),
    ("EXPORTIND",        1),
    ("ENTRYREVIEWIND",   1),
    ("WHSEREVIEWIND",    1),
    ("DROPSHIPIND",      1),
    ("ITEMS",            4),
    ("RECEIPTDATE",      8),
    ("RECEIPTTIME",      6),
    ("INBOUNDMODE",     20),
    ("TOTALTOUCHES",     4),
    ("NUMCONTRIBACTOR",  2),
    ("NUMCONTRIBWORK",   2),
    ("MAXACTORIND",      1),
    # CONTRIBACTOR: 8 chars × 25 occurrences = 200 chars
    ("CONTRIBACTOR",   200),
    ("MAXWORKIND",       1),
    # CONTRIBWORK: 20 chars × 10 occurrences = 200 chars
    ("CONTRIBWORK",    200),
    ("CALLID",          10),
    ("ASSOCREGBASE",     7),
]

EXPECTED_RECORD_LEN = sum(length for _, length in CWIPS_FIELDS)


def inspect(path, sample_rows=5):
    print(f"=== INSPECT: {path} ===")
    size = os.path.getsize(path)
    print(f"File size: {size:,} bytes")

    with open(path, "rb") as fh:
        head = fh.read(2048)

    # Detect line endings / printability
    has_lf = b"\n" in head
    has_cr = b"\r" in head
    nonprintable = sum(1 for b in head if b < 32 and b not in (9, 10, 13))
    print(f"Newlines present: LF={has_lf}, CR={has_cr}")
    print(f"Non-printable bytes in first 2 KB: {nonprintable}/{len(head)} "
          f"({nonprintable / len(head):.0%})")
    print(f"Expected record length per spec (text mode): {EXPECTED_RECORD_LEN} bytes")

    # First few "records" — either by newline if delimited, or by fixed-width
    if has_lf:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh):
                if i >= sample_rows:
                    break
                print(f"\n--- Line {i + 1} (len={len(line.rstrip())}) ---")
                print(repr(line[:200]))
    else:
        print("\nNo newlines detected — likely fixed-width with no delimiter.")
        with open(path, "rb") as fh:
            for i in range(sample_rows):
                chunk = fh.read(EXPECTED_RECORD_LEN)
                if not chunk:
                    break
                print(f"\n--- Record {i + 1} (first 200 bytes hex+ASCII) ---")
                print(chunk[:200].hex())
                printable = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk[:200])
                print(printable)


def parse_record(line):
    """Parse a single fixed-width record per CWIPS spec. Returns dict."""
    rec = {}
    offset = 0
    for name, length in CWIPS_FIELDS:
        rec[name] = line[offset:offset + length].rstrip()
        offset += length
    return rec


def parse(path, out_csv, max_records=None):
    print(f"\n=== PARSE: {path} -> {out_csv} ===")

    # Try line-delimited first
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        first = fh.readline()
    line_delimited = bool(first) and len(first.rstrip("\r\n")) >= EXPECTED_RECORD_LEN - 5

    fieldnames = [name for name, _ in CWIPS_FIELDS]
    written = 0
    inbound_counts = Counter()
    work_counts = Counter()
    per_cmf_calls = defaultdict(int)
    per_cmf_emails = defaultdict(int)

    with open(out_csv, "w", newline="", encoding="utf-8") as outfh:
        writer = csv.DictWriter(outfh, fieldnames=fieldnames)
        writer.writeheader()

        if line_delimited:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    line = line.rstrip("\r\n")
                    if len(line) < EXPECTED_RECORD_LEN - 20:
                        continue
                    rec = parse_record(line.ljust(EXPECTED_RECORD_LEN))
                    writer.writerow(rec)
                    written += 1
                    inbound_counts[rec["INBOUNDMODE"]] += 1
                    work_counts[rec["WORK"]] += 1
                    cmf = rec["SHIPTON"] or rec["CUSTOMERACCOUNT"]
                    if cmf:
                        if "PHONE" in rec["INBOUNDMODE"].upper():
                            per_cmf_calls[cmf] += 1
                        elif "EMAIL" in rec["INBOUNDMODE"].upper():
                            per_cmf_emails[cmf] += 1
                    if max_records and written >= max_records:
                        break
        else:
            with open(path, "rb") as fh:
                while True:
                    chunk = fh.read(EXPECTED_RECORD_LEN)
                    if len(chunk) < EXPECTED_RECORD_LEN:
                        break
                    line = chunk.decode("utf-8", errors="replace")
                    rec = parse_record(line)
                    writer.writerow(rec)
                    written += 1
                    inbound_counts[rec["INBOUNDMODE"]] += 1
                    work_counts[rec["WORK"]] += 1
                    cmf = rec["SHIPTON"] or rec["CUSTOMERACCOUNT"]
                    if cmf:
                        if "PHONE" in rec["INBOUNDMODE"].upper():
                            per_cmf_calls[cmf] += 1
                        elif "EMAIL" in rec["INBOUNDMODE"].upper():
                            per_cmf_emails[cmf] += 1
                    if max_records and written >= max_records:
                        break

    print(f"Parsed {written:,} records into {out_csv}")

    print("\n=== Inbound Mode distribution ===")
    for mode, n in inbound_counts.most_common(20):
        print(f"  {mode!r:<25} {n:>10,}")

    print("\n=== Top WORK types ===")
    for w, n in work_counts.most_common(15):
        print(f"  {w!r:<35} {n:>10,}")

    print("\n=== Top 20 CMFs by phone calls ===")
    for cmf, n in sorted(per_cmf_calls.items(), key=lambda x: -x[1])[:20]:
        print(f"  CMF {cmf:<10} phone={n:>6,} email={per_cmf_emails.get(cmf, 0):>6,}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="Path to CWIPS file (e.g. cwips_jan2026.TXT)")
    ap.add_argument("--inspect-only", action="store_true",
                    help="Only inspect first 5 records, don't parse the whole file")
    ap.add_argument("--out", default=None,
                    help="Output CSV path (default: <input>.parsed.csv)")
    ap.add_argument("--max", type=int, default=None,
                    help="Only parse first N records (for sanity-check)")
    args = ap.parse_args()

    inspect(args.path)
    if args.inspect_only:
        return

    out = args.out or args.path + ".parsed.csv"
    parse(args.path, out, args.max)


if __name__ == "__main__":
    main()
