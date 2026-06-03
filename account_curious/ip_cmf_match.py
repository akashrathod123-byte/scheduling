#!/usr/bin/env python3
"""
Method 3 — IP -> CMF affinity for the truly-unlinked.

Take every "Not linked to CMF" visitor, find the IP(s) they browse from, and
check whether that IP is "owned" by a CMF (i.e. other LINKED people on the same
IP belong to one company). Public/shared IPs (used by many CMFs) are excluded
automatically, so we only keep corporate-looking IPs.

Steps:
  1. Read the truly-unlinked visitor IDs from test_with_cmf_status.xlsx.
  2. Push them into a #targets temp table in the warehouse.
  3. Set-based query:
        target visitor -> visit_source.client_ip
        client_ip      -> CMFs of LINKED peers on that same IP
        keep the IP's dominant CMF only if it's dominant enough (@min_share)
        and the IP isn't shared by too many CMFs (@max_cmfs = public/ISP filter)
  4. Write one row per (visitor, ip) match + a per-visitor best pick, and print
     how many of the 108k we could resolve this way.

NOTE: the warehouse columns drifted from the design doc. This assumes
visit_source has columns client_ip and recorded_visitor_id -- run STEP 0 of
method2_3_queries.sql first and fix the two names below if they differ.

SPYDER USERS: edit CONFIG, press Run (F5).
Requires:  pip install pyodbc openpyxl
"""

import csv
from collections import defaultdict

import openpyxl
import pyodbc


# ===========================================================================
# EDIT THIS, THEN PRESS RUN (F5).
# ===========================================================================
CONFIG = {
    "status_file": r"P:\Capacity Management\Management\Akash\B2B\User Models\Account Curious\test_with_cmf_status.xlsx",
    "out_csv":     r"P:\Capacity Management\Management\Akash\B2B\User Models\Account Curious\ip_cmf_matches.csv",

    "server":   r"sqlipmds\sqlipmds",
    "database": "DigitalAnalytics",
    "driver":   "ODBC Driver 17 for SQL Server",

    # warehouse column names (fix if STEP 0 shows different ones)
    "visit_table":   "visit_source",
    "visit_ip_col":  "client_ip",
    "visit_vid_col": "recorded_visitor_id",

    # tuning
    "min_share": 0.80,   # dominant CMF must hold >= this share of linked peers on the IP
    "max_cmfs":  3,      # if an IP has more than this many CMFs, treat it as public -> skip
    "insert_batch": 5000,
}
# ===========================================================================


def read_unlinked_ids(path):
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb.active
    ids = []
    status_col = 4
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            for j, h in enumerate(row):
                if h and "status" in str(h).lower():
                    status_col = j
            continue
        if status_col < len(row) and row[status_col] == "Not linked to CMF":
            vid = row[0]
            if isinstance(vid, str) and vid.strip().isdigit():
                vid = int(vid)
            if isinstance(vid, int):
                ids.append(vid)
    wb.close()
    return ids


def main():
    print("Reading truly-unlinked visitor IDs...")
    ids = read_unlinked_ids(CONFIG["status_file"])
    print(f"  {len(ids):,} unlinked visitors to check")

    conn = pyodbc.connect(
        f"DRIVER={{{CONFIG['driver']}}};SERVER={CONFIG['server']};"
        f"DATABASE={CONFIG['database']};Trusted_Connection=yes;")
    cur = conn.cursor()

    # 1. load targets into a temp table
    print("Loading targets into #targets...")
    cur.execute("IF OBJECT_ID('tempdb..#targets') IS NOT NULL DROP TABLE #targets;")
    cur.execute("CREATE TABLE #targets (visitor_id BIGINT PRIMARY KEY);")
    cur.fast_executemany = True
    rows = [(i,) for i in set(ids)]
    n = CONFIG["insert_batch"]
    for i in range(0, len(rows), n):
        cur.executemany("INSERT INTO #targets (visitor_id) VALUES (?)", rows[i:i + n])
    conn.commit()
    print(f"  loaded {len(rows):,}")

    vt, ip, vid = CONFIG["visit_table"], CONFIG["visit_ip_col"], CONFIG["visit_vid_col"]
    min_share, max_cmfs = CONFIG["min_share"], CONFIG["max_cmfs"]

    # 2. the IP -> CMF affinity query
    print("Running IP -> CMF affinity (this can take a while)...")
    sql = f"""
    DECLARE @min_share FLOAT = {min_share};
    DECLARE @max_cmfs   INT  = {max_cmfs};

    WITH target_ip AS (
        SELECT DISTINCT t.visitor_id, v.{ip} AS client_ip
        FROM   #targets t
        JOIN   {vt} v ON v.{vid} = t.visitor_id
        WHERE  v.{ip} IS NOT NULL
    ),
    linked AS (
        SELECT DISTINCT cv.visitor_id, cc.cmf_id
        FROM   contact_visitor_source cv
        JOIN   contact_cmf_source     cc ON cc.contact_id = cv.contact_id
        WHERE  cc.cmf_id IS NOT NULL
    ),
    ip_cmf AS (
        SELECT ti.client_ip, l.cmf_id,
               COUNT(DISTINCT l.visitor_id) AS peers
        FROM   (SELECT DISTINCT client_ip FROM target_ip) ti
        JOIN   {vt} v ON v.{ip} = ti.client_ip
        JOIN   linked l ON l.visitor_id = v.{vid}
        GROUP BY ti.client_ip, l.cmf_id
    ),
    ip_summary AS (
        SELECT client_ip,
               COUNT(DISTINCT cmf_id) AS distinct_cmfs,
               SUM(peers)             AS total_peers,
               MAX(peers)             AS top_peers
        FROM   ip_cmf GROUP BY client_ip
    ),
    ip_dominant AS (
        SELECT ic.client_ip, ic.cmf_id AS suggested_cmf,
               CAST(ic.peers AS FLOAT)/s.total_peers AS share,
               s.distinct_cmfs, s.total_peers
        FROM   ip_cmf ic
        JOIN   ip_summary s ON s.client_ip = ic.client_ip
        WHERE  ic.peers = s.top_peers
          AND  CAST(ic.peers AS FLOAT)/s.total_peers >= @min_share
          AND  s.distinct_cmfs <= @max_cmfs
    )
    SELECT ti.visitor_id, ti.client_ip, d.suggested_cmf,
           d.share, d.distinct_cmfs, d.total_peers
    FROM   target_ip ti
    JOIN   ip_dominant d ON d.client_ip = ti.client_ip
    ORDER BY ti.visitor_id, d.share DESC;
    """
    cur.execute(sql)
    matches = cur.fetchall()
    conn.close()
    print(f"  {len(matches):,} (visitor, IP) matches returned")

    # 3. write raw matches + pick best CMF per visitor
    best = {}                       # visitor -> (share, cmf)
    cmfs_per_visitor = defaultdict(set)
    with open(CONFIG["out_csv"], "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["visitor_id", "client_ip", "suggested_cmf_id", "share",
                    "distinct_cmfs_on_ip", "linked_peers_on_ip"])
        for vid_, cip, cmf, share, dcmfs, peers in matches:
            w.writerow([vid_, cip, cmf, f"{share:.2f}", dcmfs, peers])
            cmfs_per_visitor[vid_].add(cmf)
            if vid_ not in best or share > best[vid_][0]:
                best[vid_] = (share, cmf)

    resolved = len(best)
    clean = sum(1 for v in cmfs_per_visitor if len(cmfs_per_visitor[v]) == 1)
    print("\n=== Method 3 results ===")
    print(f"Unlinked visitors checked:        {len(set(ids)):,}")
    print(f"Resolved to >=1 CMF via IP:       {resolved:,} "
          f"({resolved/len(set(ids))*100:.1f}%)")
    print(f"  ...with a single, clean CMF:    {clean:,}")
    print(f"  ...with conflicting CMFs (IPs):  {resolved - clean:,}")
    print(f"\nPer-match detail written to: {CONFIG['out_csv']}")


if __name__ == "__main__":
    main()
