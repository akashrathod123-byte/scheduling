/*
Rebuild the 3-Venn poster from scratch.

Produces per-signature counts (r1_hit, r2_hit, r3_hit, r4_hit → 16 buckets)
for each of the three grains: orders, contacts, CMFs. Everything runs
against ONE base filter so the numbers reconcile.

Base filter
-----------
  window   : orders in the last 12 months (added_ts)
  scope    : ship_to_cmf NOT IN 10-CMF exclusion list
             (3 legacy shared CC + 7 CREDIT CARD INDIVIDUAL shells)
             AND ship_to_cmf.listcode <> '98'
             (drop all CCI accounts — one-off card purchases, not
              the business ship-to population SLV targets. These
              would otherwise inflate R2 with 1–2 order pairs that
              aren't the customers we're trying to reach.)

Rules
-----
  R1  ship-to CMF has 10+ ordering contacts in the window
  R2  (contact, ship-to CMF) pair has fewer than 3 orders in the window
  R3  ship-to CMF listcode in {05,06,07,08,09,15,97}
  R4  (contact, ship-to CMF) pair uses more than one non-individual billto

Contact / CMF rollup
--------------------
  A contact / CMF is "hit" by a rule if ANY of its rows are hit.
  So the contact / CMF signature = MAX(hit) across the rows for that
  contact / CMF. This matches the Venn's "affected by rule X" framing.
*/

DECLARE @start datetime2 = DATEADD(month, -12, GETDATE());

DECLARE @excl TABLE (cmf_id BIGINT PRIMARY KEY);
INSERT INTO @excl VALUES
    (130387900),(12121200),(144173500),
    (99881000),(99881100),(99882000),(99882200),
    (99883000),(99883100),(99884300);

DECLARE @r3_codes TABLE (listcode varchar(4) PRIMARY KEY);
INSERT INTO @r3_codes VALUES ('05'),('06'),('07'),('08'),('09'),('15'),('97');

-- =====================================================
-- 0. What we're about to drop from the universe
--    (for a transparent CCI callout)
-- =====================================================
SELECT
    'excluded_upfront' AS scope,
    CASE
        WHEN o.ship_to_cmf IN (SELECT cmf_id FROM @excl) THEN 'shell_cmf'
        WHEN ship_c.listcode = '98'                      THEN 'cci_individual'
    END                                            AS reason,
    COUNT(*)                                       AS orders,
    COUNT(DISTINCT o.contact_id)                   AS contacts,
    COUNT(DISTINCT o.ship_to_cmf)                  AS cmfs
FROM secure.order_source o
LEFT JOIN DigitalAnalytics.dbo.customer_source ship_c
       ON ship_c.cmf_id = o.ship_to_cmf AND ship_c.mode = 'ACTIVE'
WHERE o.added_ts >= @start
  AND (o.ship_to_cmf IN (SELECT cmf_id FROM @excl) OR ship_c.listcode = '98')
GROUP BY
    CASE
        WHEN o.ship_to_cmf IN (SELECT cmf_id FROM @excl) THEN 'shell_cmf'
        WHEN ship_c.listcode = '98'                      THEN 'cci_individual'
    END;

-- =====================================================
-- 1. Base orders in window, scoped by exclusion list + listcode 98
-- =====================================================
IF OBJECT_ID('tempdb..#base') IS NOT NULL DROP TABLE #base;
SELECT
    o.wo_id,
    o.ship_to_cmf,
    o.bill_to_cmf,
    o.contact_id,
    ship_c.listcode AS ship_listcode,           -- for R3
    bill_c.listcode AS billto_listcode          -- for R4 non-individual filter
INTO #base
FROM secure.order_source o
LEFT JOIN DigitalAnalytics.dbo.customer_source ship_c
       ON ship_c.cmf_id = o.ship_to_cmf
      AND ship_c.mode   = 'ACTIVE'
LEFT JOIN DigitalAnalytics.dbo.customer_source bill_c
       ON bill_c.cmf_id = o.bill_to_cmf
      AND bill_c.mode   = 'ACTIVE'
WHERE o.added_ts    >= @start
  AND o.ship_to_cmf NOT IN (SELECT cmf_id FROM @excl)
  AND (ship_c.listcode IS NULL OR ship_c.listcode <> '98');   -- drop CCI

-- =====================================================
-- 2. CMF-level rollups (listcode already on #base)
-- =====================================================
IF OBJECT_ID('tempdb..#cmf_facts') IS NOT NULL DROP TABLE #cmf_facts;
SELECT
    b.ship_to_cmf,
    COUNT(DISTINCT b.contact_id) AS contact_count,
    MAX(b.ship_listcode)         AS cmf_listcode
INTO #cmf_facts
FROM #base b
GROUP BY b.ship_to_cmf;

-- =====================================================
-- 3. (contact, CMF)-level rollups
-- =====================================================
IF OBJECT_ID('tempdb..#cc_facts') IS NOT NULL DROP TABLE #cc_facts;
SELECT
    b.ship_to_cmf,
    b.contact_id,
    COUNT(*)                                         AS orders_at_shipto,
    COUNT(DISTINCT CASE WHEN b.billto_listcode <> '01'
                        THEN b.bill_to_cmf END)      AS distinct_nonind_billto
INTO #cc_facts
FROM #base b
GROUP BY b.ship_to_cmf, b.contact_id;

-- =====================================================
-- 4. Per-order rule flags → 4-bit signature
-- =====================================================
IF OBJECT_ID('tempdb..#flags') IS NOT NULL DROP TABLE #flags;
SELECT
    b.wo_id,
    b.ship_to_cmf,
    b.contact_id,
    CASE WHEN cf.contact_count >= 10                      THEN 1 ELSE 0 END AS r1_hit,
    CASE WHEN cc.orders_at_shipto < 3                     THEN 1 ELSE 0 END AS r2_hit,
    CASE WHEN cf.cmf_listcode IN (SELECT listcode FROM @r3_codes)
                                                          THEN 1 ELSE 0 END AS r3_hit,
    CASE WHEN cc.distinct_nonind_billto > 1               THEN 1 ELSE 0 END AS r4_hit
INTO #flags
FROM #base b
LEFT JOIN #cmf_facts cf ON cf.ship_to_cmf = b.ship_to_cmf
LEFT JOIN #cc_facts  cc ON cc.ship_to_cmf = b.ship_to_cmf
                       AND cc.contact_id  = b.contact_id;

-- =====================================================
-- 5a. ORDERS — 16-signature histogram
-- =====================================================
SELECT
    'orders' AS grain,
    r1_hit, r2_hit, r3_hit, r4_hit,
    COUNT(*) AS n
FROM #flags
GROUP BY r1_hit, r2_hit, r3_hit, r4_hit
ORDER BY r1_hit, r2_hit, r3_hit, r4_hit;

-- =====================================================
-- 5b. CONTACTS — signature = max(hit) per contact
-- =====================================================
;WITH contact_sig AS (
    SELECT
        contact_id,
        MAX(r1_hit) AS r1_hit,
        MAX(r2_hit) AS r2_hit,
        MAX(r3_hit) AS r3_hit,
        MAX(r4_hit) AS r4_hit
    FROM #flags
    GROUP BY contact_id
)
SELECT
    'contacts' AS grain,
    r1_hit, r2_hit, r3_hit, r4_hit,
    COUNT(*) AS n
FROM contact_sig
GROUP BY r1_hit, r2_hit, r3_hit, r4_hit
ORDER BY r1_hit, r2_hit, r3_hit, r4_hit;

-- =====================================================
-- 5c. CMFs — signature = max(hit) per ship-to CMF
-- =====================================================
;WITH cmf_sig AS (
    SELECT
        ship_to_cmf,
        MAX(r1_hit) AS r1_hit,
        MAX(r2_hit) AS r2_hit,
        MAX(r3_hit) AS r3_hit,
        MAX(r4_hit) AS r4_hit
    FROM #flags
    GROUP BY ship_to_cmf
)
SELECT
    'cmfs' AS grain,
    r1_hit, r2_hit, r3_hit, r4_hit,
    COUNT(*) AS n
FROM cmf_sig
GROUP BY r1_hit, r2_hit, r3_hit, r4_hit
ORDER BY r1_hit, r2_hit, r3_hit, r4_hit;

-- =====================================================
-- 6. Universe totals for the subtitle
-- =====================================================
SELECT 'universe' AS scope,
       (SELECT COUNT(*) FROM #base)                                  AS orders,
       (SELECT COUNT(DISTINCT contact_id) FROM #base)                AS contacts,
       (SELECT COUNT(DISTINCT ship_to_cmf) FROM #base)               AS cmfs;

-- Optional: check the R4 non-individual assumption
-- (do 01 listcodes really represent "individual" billtos?)
-- SELECT bill_c.listcode, COUNT(*) AS orders
-- FROM #base b
-- LEFT JOIN DigitalAnalytics.dbo.customer_source bill_c
--        ON bill_c.cmf_id = b.bill_to_cmf AND bill_c.mode = 'ACTIVE'
-- GROUP BY bill_c.listcode
-- ORDER BY orders DESC;
