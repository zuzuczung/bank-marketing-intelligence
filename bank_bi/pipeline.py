"""Transactional SQL load with independent CSV-to-SQL reconciliations."""
import hashlib
from collections import defaultdict
import psycopg
from psycopg.rows import dict_row
from .config import ROOT, database_kwargs, save
from .source import COLUMNS, rows, profile
from .rules import validate_row, dimension


def query(sql, params=None):
    with psycopg.connect(**database_kwargs(),row_factory=dict_row) as con:
        return con.execute(sql,params).fetchall()


def load():
    data=rows()
    if len(data)!=45211:raise ValueError('Source row count changed')
    for row in data:validate_row(row)
    profile(data)
    with psycopg.connect(**database_kwargs()) as con:
        con.execute((ROOT/'sql/01_staging.sql').read_text())
        con.execute('TRUNCATE staging.campaign_record')
        with con.cursor().copy('COPY staging.campaign_record FROM STDIN') as copy:
            for i,row in enumerate(data,2):
                copy.write_row((i,)+tuple(row[c] for c in COLUMNS))
        con.execute((ROOT/'sql/02_analytics.sql').read_text())
        n,yes=con.execute('SELECT count(*),sum(subscribed) FROM analytics.fact_contact').fetchone()
        if (n,yes)!=(len(data),sum(r['y']=='yes' for r in data)):
            raise RuntimeError('Load reconciliation failed; rolling back')
        sha=hashlib.sha256((ROOT/'data/raw/bank-full.csv').read_bytes()).hexdigest()
        con.execute('INSERT INTO staging.load_audit(source_sha256,source_rows,fact_rows) VALUES(%s,%s,%s)',(sha,len(data),n))
    return validate()


def validate():
    data=rows(); p=profile(data); checks=[]
    def check(name,passed,details=None):
        checks.append(dict(name=name,passed=bool(passed),details=details))
    t=query('SELECT count(*) n,sum(subscribed) yes,sum(campaign_contacts) contacts,'
            'count(*) FILTER(WHERE exact_duplicate) duplicates FROM analytics.fact_contact')[0]
    check('source_row_count',t['n']==p['rows']==45211)
    check('source_outcomes',t['yes']==p['subscribers'])
    check('source_contacts',t['contacts']==p['contacts'])
    check('duplicate_flag_reconciliation',t['duplicates']==p['exact_duplicate_excess'])
    check('unique_technical_key',query('SELECT count(*)=count(DISTINCT source_row) ok FROM analytics.fact_contact')[0]['ok'])
    check('sentinel_mapping',query('SELECT count(*) n FROM analytics.fact_contact WHERE (pdays_raw=-1) IS DISTINCT FROM (days_since_previous IS NULL)')[0]['n']==0)
    check('contact_history_consistency',query('SELECT count(*) n FROM analytics.fact_contact WHERE previously_contacted IS DISTINCT FROM (previous_contacts>0)')[0]['n']==0)
    check('unknown_channels_preserved',query("SELECT count(*) n FROM analytics.fact_contact WHERE contact='unknown'")[0]['n']==p['unknown_counts']['contact'])
    check('no_blank_source',sum(p['blank_cells'].values())==0)
    grouped={}
    for col in ['contact_label','age_band','job','education','month_label','contact_band','previous_outcome_label']:
        expected=defaultdict(lambda:[0,0,0])
        for r in data:
            v=expected[dimension(r,col)];v[0]+=1;v[1]+=r['y']=='yes';v[2]+=int(r['campaign'])
        got=query(f'SELECT {col} dimension,count(*) n,sum(subscribed) yes,sum(campaign_contacts) contacts FROM analytics.fact_contact GROUP BY 1 ORDER BY 1')
        check('independent_groups_'+col,{r['dimension']:[r['n'],r['yes'],r['contacts']] for r in got}==dict(expected),{'groups':len(got)})
        grouped[col]=got
    role=os_role()
    check('reader_select_only',query("SELECT has_table_privilege(%s,'analytics.fact_contact','SELECT') AND NOT has_table_privilege(%s,'analytics.fact_contact','INSERT,UPDATE,DELETE') AND NOT has_schema_privilege(%s,'staging','USAGE') ok",(role,role,role))[0]['ok'])
    check('empty_rate_null',query('SELECT sum(subscribed)::numeric/nullif(count(*),0) rate FROM analytics.fact_contact WHERE false')[0]['rate'] is None)
    result=dict(checks=checks,passed=sum(c['passed'] for c in checks),total=len(checks),totals=t,groups=grouped)
    save('data-validation.json',result)
    if not all(c['passed'] for c in checks):raise RuntimeError('Data checks failed: '+', '.join(c['name'] for c in checks if not c['passed']))
    print(f'Data validation: {result["passed"]}/{result["total"]} passed; {t["n"]} records, {t["yes"]} subscribed.')
    return result


def os_role():
    import os
    return os.getenv('SUPERSET_DATABASE_USER','bank_reader')
