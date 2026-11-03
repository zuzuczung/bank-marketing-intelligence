# Data contract — UCI Bank Marketing

## Scope and grain

Only `bank-full.csv`, the older 45,211-record version, is loaded. It has 16 predictors and the outcome `y`; the additional version is not mixed into the population. One record is one source row describing the client and last contact of the current campaign, not one phone call and not a verified distinct customer. No customer identifier or full year/date exists. `source_row` (starting at CSV line 2) is the technical key.

## Ingestion and cleaning rules

- Pin SHA-256, schema and expected 45,211 rows; fail closed on a changed source.
- Preserve source text in staging. Trim/lower case categorical fields for analytics; validate accepted values and numeric ranges before load.
- Preserve `unknown` as an explicit category, not zero and not a dropped row.
- Flag identical records; do not automatically delete them without a business identifier. Record duplicate count.
- `pdays=-1` means no contact in a previous campaign; convert only the derived `days_since_previous` to NULL. Keep the raw sentinel.
- Keep negative balances and high contact counts/durations, flag/report ranges; no arbitrary winsorization or outlier removal.
- No year/date is fabricated. Month charts group all observed records by month of year; no MoM/YoY claim.
- Transactional replacement of project-owned staging/analytics; preserve audit. Bootstrap refuses unowned role/database names. Superset reader gets SELECT only on analytics.

## Measures

| Measure | Definition |
|---|---|
| Bản ghi | COUNT(*) of eligible fact rows |
| Đăng ký | SUM(subscribed), y=yes |
| Tỷ lệ đăng ký | SUM(subscribed)/COUNT(*), recalculated under every filter |
| Lần liên hệ TB | SUM(campaign_contacts)/COUNT(*); includes final contact |
| Số lần liên hệ ghi nhận | SUM(campaign_contacts); a workload proxy, not a deduplicated call log |
| Từng được liên hệ | pdays >= 0; verify consistency with previous > 0 |
| Wilson 95% interval | Binomial Wilson interval, z=1.96; descriptive sampling approximation, not causal or deployment confidence |

All rates use record denominators. Unknown contact channels remain in the overall denominator. Job/education/age comparisons are descriptive; correlated attributes and selection can explain differences. `campaign` is observed by the end of the campaign, and `duration` only after the last call: neither proves that additional/longer calls cause conversion. No pre-call model, revenue, ROI or CPA is claimed because there are no costs, deposit values, exposure logs or randomized groups.

## Verification plan (defined before implementation)

1. Exact header, checksum and row count; categorical domains, integer parsing, no blank fields.
2. Unique source_row, source/fact count and outcome reconciliation; unknown and duplicate reconciliation; sentinel and contact-history rules.
3. Independently aggregate Python CSV by channel, age, job, education, month, contact band and previous outcome; compare every group with SQL.
4. Recompute every chart through Superset API and direct SQL under all-data, one channel, one month, intersected filters and an empty selection. Rates must be NULL on an empty denominator; counts may be 0.
5. Run idempotent deploy twice, compare resource IDs, inspect all tabs and native filters visually. Keep precise passed/failed/unavailable evidence; do not count API success as visual proof.
