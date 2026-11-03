CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE TABLE IF NOT EXISTS staging.campaign_record (
 source_row integer PRIMARY KEY, age text NOT NULL, job text NOT NULL,
 marital text NOT NULL, education text NOT NULL, credit_default text NOT NULL,
 balance text NOT NULL, housing text NOT NULL, loan text NOT NULL,
 contact text NOT NULL, day text NOT NULL, month text NOT NULL,
 duration text NOT NULL, campaign text NOT NULL, pdays text NOT NULL,
 previous text NOT NULL, poutcome text NOT NULL, y text NOT NULL
);
CREATE TABLE IF NOT EXISTS staging.load_audit (
 load_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 loaded_at timestamptz NOT NULL DEFAULT now(), source_sha256 text NOT NULL,
 source_rows integer NOT NULL, fact_rows integer NOT NULL
);
