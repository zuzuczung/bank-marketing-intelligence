CREATE TABLE IF NOT EXISTS analytics.fact_contact (
 source_row integer PRIMARY KEY,
 age integer NOT NULL CHECK(age > 0), age_band text NOT NULL,
 job text NOT NULL, marital text NOT NULL, education text NOT NULL,
 credit_default boolean NOT NULL, balance_eur integer NOT NULL,
 housing boolean NOT NULL, personal_loan boolean NOT NULL,
 contact text NOT NULL, contact_label text NOT NULL,
 day_of_month integer NOT NULL CHECK(day_of_month BETWEEN 1 AND 31),
 month text NOT NULL, month_number integer NOT NULL CHECK(month_number BETWEEN 1 AND 12),
 month_label text NOT NULL, duration_seconds integer NOT NULL CHECK(duration_seconds>=0),
 campaign_contacts integer NOT NULL CHECK(campaign_contacts>=1), contact_band text NOT NULL,
 pdays_raw integer NOT NULL CHECK(pdays_raw>=-1), days_since_previous integer,
 previous_contacts integer NOT NULL CHECK(previous_contacts>=0),
 previously_contacted boolean NOT NULL, previous_outcome text NOT NULL,
 previous_outcome_label text NOT NULL, subscribed integer NOT NULL CHECK(subscribed IN(0,1)),
 exact_duplicate boolean NOT NULL, record_hash text NOT NULL
);
TRUNCATE analytics.fact_contact;
INSERT INTO analytics.fact_contact
WITH normalized AS (
 SELECT source_row, age::integer age, lower(trim(job)) job, lower(trim(marital)) marital,
 lower(trim(education)) education, lower(trim(credit_default)) credit_default,
 balance::integer balance, lower(trim(housing)) housing, lower(trim(loan)) loan,
 lower(trim(contact)) contact, day::integer day_num, lower(trim(month)) month_code,
 duration::integer duration, campaign::integer campaign, pdays::integer pdays,
 previous::integer previous, lower(trim(poutcome)) poutcome, lower(trim(y)) y,
 md5(concat_ws(chr(31),age,job,marital,education,credit_default,balance,housing,loan,
 contact,day,month,duration,campaign,pdays,previous,poutcome,y)) record_hash
 FROM staging.campaign_record
), classified AS (
 SELECT *, row_number() OVER(PARTITION BY record_hash ORDER BY source_row)>1 exact_duplicate,
 array_position(ARRAY['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'],month_code) month_no
 FROM normalized
)
SELECT source_row, age,
 CASE WHEN age<30 THEN '01 · Dưới 30' WHEN age<40 THEN '02 · 30–39'
 WHEN age<50 THEN '03 · 40–49' WHEN age<60 THEN '04 · 50–59' ELSE '05 · Từ 60' END,
 job,marital,education,credit_default='yes',balance,housing='yes',loan='yes',contact,
 CASE contact WHEN 'cellular' THEN 'Di động' WHEN 'telephone' THEN 'Điện thoại bàn' ELSE 'Chưa rõ' END,
 day_num,month_code,month_no,lpad(month_no::text,2,'0') || ' · Tháng ' || month_no::text,
 duration,campaign,
 CASE WHEN campaign=1 THEN '01 · 1 lần' WHEN campaign=2 THEN '02 · 2 lần'
 WHEN campaign=3 THEN '03 · 3 lần' WHEN campaign<=5 THEN '04 · 4–5 lần'
 WHEN campaign<=10 THEN '05 · 6–10 lần' ELSE '06 · Trên 10 lần' END,
 pdays,CASE WHEN pdays=-1 THEN NULL ELSE pdays END,previous,pdays>=0,poutcome,
 CASE poutcome WHEN 'success' THEN 'Thành công' WHEN 'failure' THEN 'Thất bại'
 WHEN 'other' THEN 'Khác' ELSE 'Chưa rõ' END,(y='yes')::integer,exact_duplicate,record_hash
FROM classified;
CREATE INDEX IF NOT EXISTS fact_contact_channel ON analytics.fact_contact(contact);
CREATE INDEX IF NOT EXISTS fact_contact_month ON analytics.fact_contact(month_number);
CREATE INDEX IF NOT EXISTS fact_contact_job ON analytics.fact_contact(job);
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA staging FROM PUBLIC,bank_reader;
GRANT USAGE ON SCHEMA analytics TO bank_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO bank_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT SELECT ON TABLES TO bank_reader;
ANALYZE analytics.fact_contact;
