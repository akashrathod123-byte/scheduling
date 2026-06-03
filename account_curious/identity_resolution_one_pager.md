# Account Curious — Identity Resolution: closing the "login without a CMF" gap

**Owner:** Akash Rathod · **Date:** 2026-06-03 · **Status:** Draft for review

---

## The problem

We have a large population of customers who **log in** to our digital publications but
whose contact record is **not linked to a CMF** (Customer Master File — the company
account record). Because the link is missing, these users silently lose account-level
benefits:

- **Shared order history** across their company
- **"Purple links"** (visited/known-product cues that depend on identity + history)
- **Search by customer reference / part numbers**
- Account pricing, saved collections, and other CMF-gated experiences

They have a login but, to our systems, no company — so the experience degrades and we
can't measure or serve them as the accounts they actually are.

## Current state (from the no-CMF sample, validated against the warehouse)

> Source: `visitor_no_cmf_email_link` sample, de-duplicated to distinct visitors and
> run through the CMF-status script to strip false positives.

| Metric | Value |
|---|---|
| Distinct logged-in visitors **not linked to a CMF** | **~140,961** |
| …on a **corporate email domain** (addressable) | **104,900 (74.4%)** |
| …on **consumer/free mail** (gmail, yahoo, qq…) | 36,460 (25.9%) |
| Distinct corporate domains involved | 51,673 |
| Domains with **≥2** unlinked people (domain-match leverage) | 10,795 domains → **64,338 people (61% of corporate)** |
| Companies needed to cover **50%** of corporate volume | just **4,932** |

**Read:** three-quarters of the gap is corporate email we can reason about, and it's
concentrated — a few thousand companies cover half the volume, so a targeted backend
fix has outsized reach.

## The opportunity / hypothesis

> **If we connect these users to their CMF on the backend, their behavior improves and
> their experience gets easier** — more order-history use, more reference/part search,
> more repeat logins, higher order success — without them doing anything.

We propose a **controlled test**: link a matchable cohort to their CMF, hold out a
control, and measure the behavioral lift.

---

## Methodology — an identity-resolution waterfall

We resolve identities in **confidence order** and stop at the first confident match.
Each tier is independently measurable on the samples we already have.

| # | Method | What it catches | Confidence | Data we need |
|---|--------|-----------------|-----------|--------------|
| **1** | **Domain → CMF affinity.** A corporate domain where *other* contacts at the company are already linked to a CMF → map the unlinked user to that CMF. | Bulk of the 74% corporate population | High (single-CMF domains) → Medium (multi-CMF domains, needs branch/geo tiebreak) | `with_contacts` file + CMF status (script provided) |
| **2** | **Visitor → warehouse identity stitch.** Follow `visitor_id → contact_visitor_source → contact_id` and check for *other* signals on the contact (other linked visitor_ids, order/account references) that resolve a CMF. | Users whose contact is partially known | High | `contact_visitor_source`, order/account tables |
| **3** | **IP / firmographic match.** `visit_source.client_ip` → corporate egress IP ranges → company → CMF. | The **26% on consumer email** browsing from a corporate network — otherwise unreachable | Medium (needs IP→firmographic source) | `visit_source` + IP intelligence |
| **4** | **Email-on-record match.** The exact email already exists on a CMF-linked contact under a *different* visitor/contact id → stitch them. | Duplicate identities | High | contact/email table |
| **5** | **Order / account-number match.** User placed orders or entered an account ref tied to a CMF. | Active buyers | Very high | order history / `customer_source` |
| **6** | **Self-serve confirmation.** Prompt the user to claim their company (we already track `onboarding_form_save_engagement_count`). | Long-tail + consumer-email users | Customer-verified | onboarding form |

**Coverage logic:** Methods 1, 4, 5 are highest confidence and cheapest; Method 3
unlocks the consumer-email segment; Method 6 mops up the long tail with zero false
positives. Running 1→5 systematically should resolve the large majority of the
corporate population, with 3 + 6 reaching into the consumer-email 26%.

---

## Proposed test design

1. **Build the matchable cohort** — Method 1 high-confidence matches (corporate domain
   with exactly one dominant CMF). Largest, cleanest pool.
2. **Randomize** into **Treatment** (link to CMF on the backend) vs **Control** (hold out).
3. **Measure** over a fixed window (e.g. 6–8 weeks), pre vs post, treatment vs control,
   using `visit_source` engagement counts already in the warehouse:
   - `order_history_engagement_count`, `save_order_engagement_count`
   - `place_order_success_count`, `has_place_order_success`
   - reference / `part_number_engagement_count`, search success & **ease** (time/ clicks to first success)
   - `login_engagement_count` / repeat-visit frequency
   - saved collections / shared-link usage (the "purple link" benefit)
4. **Success criterion:** statistically significant lift in treatment vs control on the
   primary metrics (order-history use + order success), with no degradation in others.

---

## Recommendations

1. **Run the Method-1 matcher now** (`domain_affinity_match.py`) to quantify the
   single biggest lever: *what % of the 104,900 corporate users we can confidently map
   by domain.* This number sizes the whole program.
2. **Greenlight the backend-link A/B test** on the high-confidence cohort — low risk
   (reversible), high signal, directly proves the benefit story.
3. **Stand up Method 3 (IP→firmographic)** as a fast follow to reach the consumer-email
   26% that domain matching can't touch.
4. **Prioritize by concentration** — the top ~5k companies cover half the volume; fix
   those first for fastest impact.
5. **Add a self-serve "confirm your company" prompt** for the irreducible long tail —
   zero-false-positive and improves data quality going forward.

## Open questions / risks

- **Multi-CMF domains** (large enterprises, distributors) need a tiebreak rule
  (branch, geo/zip from `marketing_source`, or most-common CMF). Quantify how many
  domains are multi-CMF before auto-linking.
- **Consumer-email-from-corp-IP** is the hardest segment; depends on having an
  IP→company source.
- Auto-linking must be **reversible** and respect any privacy/consent constraints.
