"""Compare all persisted Superset chart bindings with direct SQL under filters."""
import json
import math
from .api import API
from .config import ROOT,save
from .pipeline import query
from .dashboard_spec import METRICS,visuals,context

SCENARIOS={
 'all':[],
 'mobile':[{'col':'contact_label','op':'IN','val':['Di động']}],
 'may':[{'col':'month_label','op':'IN','val':['05 · Tháng 5']}],
 'mobile_may':[{'col':'contact_label','op':'IN','val':['Di động']},{'col':'month_label','op':'IN','val':['05 · Tháng 5']}],
 'student_mobile':[{'col':'job','op':'IN','val':['student']},{'col':'contact_label','op':'IN','val':['Di động']}],
 'empty':[{'col':'contact_label','op':'IN','val':['__empty_contract_test__']}],
}


def same(a,b):
    if a is None or b is None:return a is None and b is None
    if isinstance(a,(int,float)) or isinstance(b,(int,float)):
        return math.isclose(float(a),float(b),rel_tol=1e-8,abs_tol=1e-9)
    return str(a)==str(b)


def main():
    state=json.loads((ROOT/'artifacts/deployment.json').read_text());api=API();checks=[]
    dashboard=api.request('GET',f'dashboard/{state["dashboard_id"]}')['result']
    meta=json.loads(dashboard['json_metadata']);nf=meta['native_filter_configuration']
    if len(nf)!=3 or any(set(f['chartsInScope'])!=set(state['charts'].values()) for f in nf):
        raise RuntimeError('Native filter scope mismatch')
    for item in visuals():
        ident=state['charts'][item['key']]
        saved=api.request('GET',f'chart/{ident}')['result']
        saved_ctx=json.loads(saved['query_context']);params=json.loads(saved['params'])
        ms=item.get('metrics',[item['metric']]);dim=item['dimension']
        if saved_ctx['queries'][0]['metrics']!=ms or params['datasource']!=f'{state["dataset_id"]}__table':
            raise RuntimeError('Persisted chart binding mismatch')
        for label,filters in SCENARIOS.items():
            ctx=json.loads(json.dumps(saved_ctx));ctx['queries'][0]['filters']=filters
            ctx['force']=True
            r=api.request('POST','chart/data',json=ctx)
            result=r['result'][0]
            if result.get('error') or result.get('status')=='failed':
                raise RuntimeError(f'Chart query failed: {item["key"]}/{label}')
            actual=result['data'];cols=[dim] if dim else []
            select=cols+[f'{METRICS[m][1]} AS "{m}"' for m in ms]
            predicates=[];values=[]
            for f in filters:
                if f['col'] not in ['contact_label','month_label','job']:raise ValueError('Unexpected filter')
                predicates.append(f'"{f["col"]}" = ANY(%s)');values.append(f['val'])
            sql='SELECT '+','.join(select)+' FROM analytics.fact_contact'
            if predicates:sql+=' WHERE '+' AND '.join(predicates)
            if dim:sql+=' GROUP BY '+dim
            expected=query(sql,values)
            actual_by_key={str(row.get(dim,'')):row for row in actual}
            expected_by_key={str(row.get(dim,'')):row for row in expected}
            passed=set(actual_by_key)==set(expected_by_key)
            if passed:
                passed=all(same(actual_by_key[k].get(m),v[m]) for k,v in expected_by_key.items() for m in ms)
            checks.append(dict(chart=item['key'],scenario=label,passed=passed,
                actual_groups=len(actual),expected_groups=len(expected)))
    out=dict(passed=sum(c['passed'] for c in checks),total=len(checks),native_filters=3,checks=checks)
    save('chart-validation.json',out)
    if not all(c['passed'] for c in checks):
        bad=[f'{c["chart"]}/{c["scenario"]}' for c in checks if not c['passed']]
        raise RuntimeError('Chart reconciliation failed: '+', '.join(bad))
    print(f'Superset vs SQL: {out["passed"]}/{out["total"]} passed.')
    return out


if __name__=='__main__':main()
