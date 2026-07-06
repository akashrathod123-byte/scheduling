/*
Universe delta from adding the 7 CCI shell CMFs to the exclusion list.

Compares "current universe" (excluding only the original 3 shared CC CMFs)
against "proposed universe" (also excluding the 7 CREDIT CARD INDIVIDUAL
shell CMFs discovered on 2026-07-06).

Reports the drop for each of the three Venn totals: orders, contacts, CMFs
in the 12-month window.
*/

-- The two exclusion sets
DECLARE @orig  TABLE (cmf_id BIGINT);
INSERT INTO @orig VALUES (130387900),(12121200),(144173500);

DECLARE @full  TABLE (cmf_id BIGINT);
INSERT INTO @full VALUES (130387900),(12121200),(144173500),
                         (99881000),(99881100),(99882000),(99882200),
                         (99883000),(99883100),(99884300);

-- =====================================================
-- ORDERS: 12-month window
-- =====================================================
SELECT 'orders' AS grain,
       (SELECT COUNT(*)
          FROM secure.order_source o
         WHERE o.added_ts >= DATEADD(month, -12, GETDATE())
           AND o.ship_to_cmf NOT IN (SELECT cmf_id FROM @orig)) AS current_universe,
       (SELECT COUNT(*)
          FROM secure.order_source o
         WHERE o.added_ts >= DATEADD(month, -12, GETDATE())
           AND o.ship_to_cmf NOT IN (SELECT cmf_id FROM @full)) AS proposed_universe;

-- =====================================================
-- CONTACTS: distinct ordering contacts in the 12-month window
-- =====================================================
SELECT 'contacts' AS grain,
       (SELECT COUNT(DISTINCT o.contact_id)
          FROM secure.order_source o
         WHERE o.added_ts >= DATEADD(month, -12, GETDATE())
           AND o.ship_to_cmf NOT IN (SELECT cmf_id FROM @orig)) AS current_universe,
       (SELECT COUNT(DISTINCT o.contact_id)
          FROM secure.order_source o
         WHERE o.added_ts >= DATEADD(month, -12, GETDATE())
           AND o.ship_to_cmf NOT IN (SELECT cmf_id FROM @full)) AS proposed_universe;

-- =====================================================
-- CMFs: distinct ship-to CMFs that received an order in the 12-month window
-- =====================================================
SELECT 'cmfs' AS grain,
       (SELECT COUNT(DISTINCT o.ship_to_cmf)
          FROM secure.order_source o
         WHERE o.added_ts >= DATEADD(month, -12, GETDATE())
           AND o.ship_to_cmf NOT IN (SELECT cmf_id FROM @orig)) AS current_universe,
       (SELECT COUNT(DISTINCT o.ship_to_cmf)
          FROM secure.order_source o
         WHERE o.added_ts >= DATEADD(month, -12, GETDATE())
           AND o.ship_to_cmf NOT IN (SELECT cmf_id FROM @full)) AS proposed_universe;

-- =====================================================
-- Just the CCI-shell contribution, for a clean callout number
-- =====================================================
SELECT 'cci_shells_only' AS scope,
       COUNT(*)                                AS orders,
       COUNT(DISTINCT contact_id)              AS contacts,
       COUNT(DISTINCT ship_to_cmf)             AS cmfs
FROM secure.order_source
WHERE added_ts >= DATEADD(month, -12, GETDATE())
  AND ship_to_cmf IN (99881000,99881100,99882000,99882200,
                      99883000,99883100,99884300);
