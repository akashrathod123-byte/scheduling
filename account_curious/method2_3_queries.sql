/* =====================================================================
   Account Curious — Identity Resolution, Methods 2 & 3 (SQL Server)
   Server:  sqlipmds\sqlipmds      Database: DigitalAnalytics
   ---------------------------------------------------------------------
   NOTE: the data-warehouse PDF column names have drifted from the live
   tables (e.g. 'cmf_role' didn't exist). RUN STEP 0 FIRST and fix any
   column names below that don't match (esp. visit_source.client_ip and
   visit_source.recorded_visitor_id).
   ===================================================================== */
USE DigitalAnalytics;

/* ---------------------------------------------------------------------
   STEP 0 — discover the real column names before trusting the doc.
   --------------------------------------------------------------------- */
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM   INFORMATION_SCHEMA.COLUMNS
WHERE  TABLE_NAME IN ('visit_source',
                      'contact_visitor_source',
                      'contact_cmf_source',
                      'customer_source')
ORDER BY TABLE_NAME, ORDINAL_POSITION;


/* ---------------------------------------------------------------------
   STEP 1 — load the target visitors (the "no CMF" list) into #targets.

   Pick ONE of these ways to populate it:
     (a) the Python loader bulk-inserts into ##targets, or
     (b) BULK INSERT from the CSV, or
     (c) if the list already lives in a table, SELECT INTO.
   For a quick manual test you can just insert a few ids by hand.
   --------------------------------------------------------------------- */
IF OBJECT_ID('tempdb..#targets') IS NOT NULL DROP TABLE #targets;
CREATE TABLE #targets (visitor_id BIGINT PRIMARY KEY);

-- quick manual test rows (replace with the real load):
INSERT INTO #targets (visitor_id) VALUES (8731349095930), (9363319698432);


/* =====================================================================
   METHOD 2 — Visitor -> contact -> CMF stitch
   ---------------------------------------------------------------------
   A visitor can map to MORE THAN ONE contact_id in contact_visitor_source.
   The "no CMF" extract may have keyed off a contact that lacks a CMF while
   ANOTHER contact for the same visitor IS linked. This recovers those.
   Also re-checks live data (catches stale false-positives).
   ===================================================================== */
SELECT
    t.visitor_id,
    COUNT(DISTINCT cv.contact_id)                       AS contact_ids,
    COUNT(DISTINCT cc.cmf_id)                           AS distinct_cmfs_found,
    MAX(cc.cmf_id)                                      AS example_cmf_id,
    CASE
        WHEN COUNT(cc.cmf_id) = 0 THEN 'still no CMF (try Method 3)'
        WHEN COUNT(DISTINCT cc.cmf_id) = 1 THEN 'RECOVERED - single CMF via contact'
        ELSE 'RECOVERED - multiple CMFs (needs tiebreak)'
    END                                                 AS method2_result
FROM        #targets               AS t
LEFT JOIN   contact_visitor_source AS cv ON cv.visitor_id = t.visitor_id
LEFT JOIN   contact_cmf_source     AS cc ON cc.contact_id = cv.contact_id
GROUP BY    t.visitor_id;


/* =====================================================================
   METHOD 3 — IP -> CMF affinity (no external IP-intelligence needed)
   ---------------------------------------------------------------------
   Idea: build, from EVERY linked visitor, a map of client_ip -> CMF. A
   corporate egress IP will be dominated by a single CMF; a public/ISP IP
   will be shared by many CMFs (so we exclude it). Then assign each target
   visitor the dominant CMF of the IP(s) they browse from.
   This is what reaches consumer-email users who browse from work.

   Tunables: @min_share (how dominant a CMF must be on an IP) and
             @max_cmfs  (max distinct CMFs an IP can have to be "corporate").
   ===================================================================== */
DECLARE @min_share FLOAT = 0.80;
DECLARE @max_cmfs   INT  = 3;

WITH
-- distinct (ip, visitor) pairs from the visits table
visit_ip AS (
    SELECT DISTINCT
           v.client_ip                AS client_ip,
           v.recorded_visitor_id      AS visitor_id
    FROM   visit_source AS v
    WHERE  v.client_ip IS NOT NULL
),
-- every visitor that IS linked to a CMF, with its CMF
linked AS (
    SELECT DISTINCT cv.visitor_id, cc.cmf_id
    FROM   contact_visitor_source AS cv
    JOIN   contact_cmf_source     AS cc ON cc.contact_id = cv.contact_id
    WHERE  cc.cmf_id IS NOT NULL
),
-- how many distinct linked visitors of each CMF appear on each IP
ip_cmf AS (
    SELECT vi.client_ip,
           l.cmf_id,
           COUNT(DISTINCT l.visitor_id) AS linked_visitors
    FROM   visit_ip vi
    JOIN   linked   l ON l.visitor_id = vi.visitor_id
    GROUP BY vi.client_ip, l.cmf_id
),
-- per-IP totals so we can compute dominance and filter public IPs
ip_summary AS (
    SELECT client_ip,
           COUNT(DISTINCT cmf_id)  AS distinct_cmfs,
           SUM(linked_visitors)    AS total_linked,
           MAX(linked_visitors)    AS top_cmf_visitors
    FROM   ip_cmf
    GROUP BY client_ip
),
-- the dominant CMF per IP, kept only if it's "corporate-looking"
ip_dominant AS (
    SELECT ic.client_ip,
           ic.cmf_id                                              AS dominant_cmf,
           CAST(ic.linked_visitors AS FLOAT) / s.total_linked     AS dominant_share,
           s.distinct_cmfs,
           s.total_linked
    FROM   ip_cmf      ic
    JOIN   ip_summary  s  ON s.client_ip = ic.client_ip
    WHERE  ic.linked_visitors = s.top_cmf_visitors           -- the top CMF
      AND  CAST(ic.linked_visitors AS FLOAT) / s.total_linked >= @min_share
      AND  s.distinct_cmfs <= @max_cmfs                      -- exclude public IPs
)
SELECT
    t.visitor_id,
    d.client_ip,
    d.dominant_cmf      AS suggested_cmf_id,
    d.dominant_share,
    d.distinct_cmfs,
    d.total_linked      AS linked_peers_on_ip
FROM        #targets   AS t
JOIN        visit_ip   AS vi ON vi.visitor_id = t.visitor_id
JOIN        ip_dominant AS d ON d.client_ip   = vi.client_ip
ORDER BY    t.visitor_id, d.dominant_share DESC;


/* ---------------------------------------------------------------------
   COVERAGE SUMMARY — how many targets does Method 3 resolve?
   --------------------------------------------------------------------- */
-- (re-uses the same logic; wrap the SELECT above in a CTE named m3 and run:)
-- SELECT COUNT(DISTINCT visitor_id) AS resolved_by_method3 FROM m3;
