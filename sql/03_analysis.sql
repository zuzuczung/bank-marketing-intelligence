-- Weighted rates: record grain, not distinct people. No causal claim.
SELECT count(*) AS records, sum(subscribed) AS subscriptions,
 sum(subscribed)::numeric/nullif(count(*),0) AS conversion_rate,
 avg(campaign_contacts) AS avg_contacts
FROM analytics.fact_contact;

-- Always inspect denominator alongside segment rate.
SELECT contact_label, count(*) AS records, sum(subscribed) AS subscriptions,
 sum(subscribed)::numeric/nullif(count(*),0) AS conversion_rate
FROM analytics.fact_contact GROUP BY contact_label ORDER BY records DESC;

SELECT contact_band, count(*) AS records, sum(subscribed) AS subscriptions,
 sum(subscribed)::numeric/nullif(count(*),0) AS conversion_rate
FROM analytics.fact_contact GROUP BY contact_band ORDER BY contact_band;

SELECT previous_outcome_label, count(*) AS records, sum(subscribed) AS subscriptions,
 sum(subscribed)::numeric/nullif(count(*),0) AS conversion_rate
FROM analytics.fact_contact GROUP BY previous_outcome_label ORDER BY records DESC;

-- Calendar month pooled across years; month field has no year.
SELECT month_label,count(*) AS records,sum(subscribed) AS subscriptions,
 sum(subscribed)::numeric/nullif(count(*),0) AS conversion_rate
FROM analytics.fact_contact GROUP BY month_label ORDER BY month_label;
