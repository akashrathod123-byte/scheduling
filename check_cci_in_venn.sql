/*
Where do CCI (listcode 98) CMFs land in the SLV Venn today?

The Venn diagrams use these rules:
  R1 = shipping location has 10+ active ordering contacts
  R2 = any contact at the ship-to has <3 orders there
  R3 = listcode in (05, 06, 07, 08, 09, 15, 97)     -- 98 is NOT in this list
  R4 = any contact at the ship-to uses >1 non-individual billto

Because 98 is NOT in R3, a listcode-98 CMF is only caught if it also
trips R1, R2, or R4. This script buckets listcode-98 CMFs into the same
9 Venn regions we show on the poster so you can see where they're
currently being counted.

Grain: CMFs. Duplicate the pattern for contacts / orders if needed.
Adjust schema names to whatever we're using in the sprint (dbo.customer_source,
secure.order_source, and the three shared shell CMFs to exclude).
*/

DECLARE @SHARED_CC_CMF1 BIGINT = 130387900;
DECLARE @SHARED_CC_CMF2 BIGINT = 12121200;
DECLARE @SHARED_CC_CMF3 BIGINT = 144173500;

-- =====================================================
-- Step 1. Per-CMF flags for listcode 98 only
-- =====================================================
WITH cci_cmfs AS (
    SELECT
        cmf_id,
        listcode
    FROM DigitalAnalytics.dbo.customer_source
    WHERE mode = 'ACTIVE'
      AND listcode = '98'
      AND cmf_id NOT IN (@SHARED_CC_CMF1, @SHARED_CC_CMF2, @SHARED_CC_CMF3)
),
-- R1: contact count at the CMF (ship-to)
r1_flags AS (
    SELECT
        c.cmf_id,
        COUNT(DISTINCT o.contact_id) AS contact_count
    FROM cci_cmfs c
    LEFT JOIN secure.order_source o
        ON o.ship_to_cmf_id = c.cmf_id
        -- 12-month window used in the poster
        AND o.order_date >= DATEADD(month, -12, GETDATE())
    GROUP BY c.cmf_id
),
-- R2: any contact at the CMF has <3 orders there
r2_flags AS (
    SELECT
        c.cmf_id,
        MAX(CASE WHEN per_contact.orders_at_shipto < 3 THEN 1 ELSE 0 END) AS r2_hit
    FROM cci_cmfs c
    LEFT JOIN (
        SELECT
            ship_to_cmf_id AS cmf_id,
            contact_id,
            COUNT(*) AS orders_at_shipto
        FROM secure.order_source
        WHERE order_date >= DATEADD(month, -12, GETDATE())
        GROUP BY ship_to_cmf_id, contact_id
    ) per_contact
        ON per_contact.cmf_id = c.cmf_id
    GROUP BY c.cmf_id
),
-- R4: any contact uses >1 non-individual billto
r4_flags AS (
    SELECT
        c.cmf_id,
        MAX(CASE WHEN per_contact.distinct_billto > 1 THEN 1 ELSE 0 END) AS r4_hit
    FROM cci_cmfs c
    LEFT JOIN (
        SELECT
            ship_to_cmf_id AS cmf_id,
            contact_id,
            COUNT(DISTINCT bill_to_cmf_id) AS distinct_billto
        FROM secure.order_source
        WHERE order_date >= DATEADD(month, -12, GETDATE())
          AND bill_to_listcode <> '01'    -- non-individual only; confirm listcode
        GROUP BY ship_to_cmf_id, contact_id
    ) per_contact
        ON per_contact.cmf_id = c.cmf_id
    GROUP BY c.cmf_id
),
flags AS (
    SELECT
        c.cmf_id,
        CASE WHEN COALESCE(r1.contact_count, 0) >= 10 THEN 1 ELSE 0 END AS r1_hit,
        COALESCE(r2.r2_hit, 0) AS r2_hit,
        0                       AS r3_hit,     -- 98 never trips R3
        COALESCE(r4.r4_hit, 0) AS r4_hit
    FROM cci_cmfs c
    LEFT JOIN r1_flags r1 ON r1.cmf_id = c.cmf_id
    LEFT JOIN r2_flags r2 ON r2.cmf_id = c.cmf_id
    LEFT JOIN r4_flags r4 ON r4.cmf_id = c.cmf_id
)

-- =====================================================
-- Step 2. Bucket into the 9 Venn regions + eligible pool
-- =====================================================
SELECT
    CASE
        WHEN r1_hit = 0 AND r2_hit = 0 AND r3_hit = 0 AND r4_hit = 0 THEN 'ELIGIBLE (passes all rules)'
        WHEN r1_hit + r2_hit + r3_hit + r4_hit >= 3                  THEN '3+ RULES'
        WHEN r3_hit = 1 AND r1_hit = 1                               THEN 'R3 ∩ R1'
        WHEN r3_hit = 1 AND r4_hit = 1                               THEN 'R3 ∩ R4'
        WHEN r4_hit = 1 AND r2_hit = 1                               THEN 'R4 ∩ R2'
        WHEN r1_hit = 1 AND r2_hit = 1                               THEN 'R1 ∩ R2'
        WHEN r1_hit = 1                                              THEN 'R1 ONLY'
        WHEN r2_hit = 1                                              THEN 'R2 ONLY'
        WHEN r3_hit = 1                                              THEN 'R3 ONLY'
        WHEN r4_hit = 1                                              THEN 'R4 ONLY'
    END AS venn_region,
    COUNT(*) AS cci_cmfs
FROM flags
GROUP BY
    CASE
        WHEN r1_hit = 0 AND r2_hit = 0 AND r3_hit = 0 AND r4_hit = 0 THEN 'ELIGIBLE (passes all rules)'
        WHEN r1_hit + r2_hit + r3_hit + r4_hit >= 3                  THEN '3+ RULES'
        WHEN r3_hit = 1 AND r1_hit = 1                               THEN 'R3 ∩ R1'
        WHEN r3_hit = 1 AND r4_hit = 1                               THEN 'R3 ∩ R4'
        WHEN r4_hit = 1 AND r2_hit = 1                               THEN 'R4 ∩ R2'
        WHEN r1_hit = 1 AND r2_hit = 1                               THEN 'R1 ∩ R2'
        WHEN r1_hit = 1                                              THEN 'R1 ONLY'
        WHEN r2_hit = 1                                              THEN 'R2 ONLY'
        WHEN r3_hit = 1                                              THEN 'R3 ONLY'
        WHEN r4_hit = 1                                              THEN 'R4 ONLY'
    END
ORDER BY cci_cmfs DESC;

-- The R3 ONLY / R3 ∩ * rows should be 0 by construction (98 isn't in R3).
-- Everything else tells you where CCI is being caught today.
