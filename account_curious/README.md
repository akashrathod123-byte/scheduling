# Account Curious — Domain / CMF coverage

Roll the visitor email exports up **by company** (using the email domain) to see
how many emails/logins each company has, and how many of those are **not linked
to a CMF** (Customer Master File — the company account record).

Produces lines like:

> **spacex.com has 87 emails and 23 of them are not linked to the CMF (26%).**

## The two inputs

| File | What it is | Role |
|------|------------|------|
| `visitor_with_contacts_email_link.csv` | Everyone we know who has logged in over the trailing window (has a contact + email) | **Total** pool of emails per company (the denominator) |
| `visitor_no_cmf_email_link.csv` | Visitors with a contact_id but **not** linked to a CMF | The **not-linked** set (the numerator) |

Each file just needs a `Visitor ID` column and an `Email` column; the company is
derived from the email domain. Sub-domains roll up to the company
(`stores.fastenal.com` + `fastenal.com` → `fastenal.com`, `its.jnj.com` →
`jnj.com`). Free/consumer mailboxes (gmail, yahoo, qq.com, outlook, …) are not
companies, so they're excluded from the main report (written to a separate
`*_consumer.csv` instead).

## Run it

```bash
# full picture (X of Y not linked):
python3 domain_cmf_analysis.py \
    --no-cmf        visitor_no_cmf_email_link.csv \
    --with-contacts visitor_with_contacts_email_link.csv \
    --out           company_cmf_coverage.csv

# only the no-cmf file (not-linked counts per company; totals left blank):
python3 domain_cmf_analysis.py --no-cmf visitor_no_cmf_email_link.csv
```

Pure Python standard library — no `pip install` needed.

### Useful options

| Flag | Default | Meaning |
|------|---------|---------|
| `--out` | `company_cmf_coverage.csv` | Output CSV path |
| `--top` | `30` | How many companies to print on screen |
| `--min-emails` | `1` | Only report companies with at least this many not-linked emails |
| `--sort-by` | `not_linked` | Ranking for the summary: `not_linked`, `total`, or `pct` |
| `--include-consumer` | off | Keep gmail/yahoo/qq/etc. in the company report |

## Output columns

| Column | Meaning |
|--------|---------|
| `company_domain` | Registered domain (the company) |
| `total_emails` | Distinct visitors at the company (from with-contacts) |
| `linked_to_cmf` | `total_emails − not_linked_to_cmf` |
| `not_linked_to_cmf` | Distinct visitors with no CMF link (from no-cmf) |
| `pct_not_linked` | `not_linked_to_cmf / total_emails` |
| `total_login_records` | Raw row count (a visitor can have >1 email) |
| `not_linked_login_records` | Raw row count from the no-cmf file |

Counts are **distinct Visitor IDs**, matching the "Count of Visitor ID" pivot in
the source workbooks; the `*_login_records` columns expose the raw rows for
transparency.

## Notes / tuning

- The consumer-domain blocklist and the multi-label TLD list (`co.uk`,
  `com.au`, …) live at the top of `domain_cmf_analysis.py` — extend them as you
  find new providers or country domains.
- Some "company" domains are really institutions you may want to treat
  separately (`*.mil`, `*.gov`, `*.edu`). They're kept in the report; filter the
  output CSV if you only want commercial accounts.
