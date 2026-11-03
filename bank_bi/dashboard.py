"""Idempotent project-owned Superset deployment. No edits to other dashboards."""
import json
import os
from urllib.parse import quote
from .api import API,uid
from .config import ROOT,MARKER,save
from .dashboard_spec import METRICS,LABELS,PAGES,NAVY,TEAL,BLUE,AMBER,visuals,form,context

SLUG='bank-marketing-intelligence'


def layout(charts):
    pos={'DASHBOARD_VERSION_KEY':'v2',
      'ROOT_ID':dict(id='ROOT_ID',type='ROOT',children=['GRID_ID']),
      'GRID_ID':dict(id='GRID_ID',type='GRID',children=['TABS-BANK'],parents=['ROOT_ID']),
      'TABS-BANK':dict(id='TABS-BANK',type='TABS',children=[],parents=['ROOT_ID','GRID_ID'],meta={})}
    for p in PAGES:
        tab='TAB-BANK-'+p['key'];parents=['ROOT_ID','GRID_ID','TABS-BANK']
        pos['TABS-BANK']['children'].append(tab)
        pos[tab]=dict(id=tab,type='TAB',children=[],parents=parents,meta={'text':p['title']})
        row='ROW-NOTE-'+p['key'];note='NOTE-'+p['key'];pos[tab]['children'].append(row)
        pos[row]=dict(id=row,type='ROW',children=[note],parents=parents+[tab],meta={'background':'BACKGROUND_TRANSPARENT'})
        pos[note]=dict(id=note,type='MARKDOWN',children=[],parents=parents+[tab,row],meta={'code':p['note'],'width':12,'height':10})
        for j,items in enumerate(p['rows']):
            row=f'ROW-{p["key"]}-{j}';pos[tab]['children'].append(row)
            pos[row]=dict(id=row,type='ROW',children=[],parents=parents+[tab],meta={'background':'BACKGROUND_TRANSPARENT'})
            for item in items:
                ident=charts[item['key']];node=f'CHART-{ident}';pos[row]['children'].append(node)
                height=25 if item['kind']=='kpi' else 56 if item['kind']=='table' else 53
                pos[node]=dict(id=node,type='CHART',children=[],parents=parents+[tab,row],meta=dict(chartId=ident,
                    uuid=uid('chart:'+item['key']),sliceName=item['title'],width=item.get('width',12//len(items)),height=height))
    return pos


def filters(ds,charts):
    result=[]
    for col,label in [('contact_label','Kênh liên hệ'),('month_label','Tháng lịch (gộp năm)'),('job','Nghề nghiệp')]:
        result.append(dict(id='NATIVE_FILTER-BANK-'+col,type='NATIVE_FILTER',name=label,filterType='filter_select',
          targets=[{'datasetId':ds,'column':{'name':col}}],
          defaultDataMask={'extraFormData':{},'filterState':{},'ownState':{}},cascadeParentIds=[],
          controlValues={'enableEmptyFilter':False,'multiSelect':True,'searchAllOptions':True,'inverseSelection':False},
          scope={'rootPath':['ROOT_ID'],'excluded':[]},chartsInScope=list(charts.values()),
          tabsInScope=['TAB-BANK-'+p['key'] for p in PAGES]))
    return result


def main():
    api=API();name='Bank Marketing Intelligence';identity=uid('database:bank')
    existing=[d for d in api.all('database') if d['uuid']==identity]
    if any(d['database_name']==name and d['uuid']!=identity for d in api.all('database')):
        raise RuntimeError('Unowned database name collision')
    user=quote(os.environ['SUPERSET_DATABASE_USER'],safe='');pw=quote(os.environ['SUPERSET_DATABASE_PASSWORD'],safe='')
    host=os.getenv('SUPERSET_PGHOST','host.docker.internal');port=os.getenv('PGPORT','5432')
    uri=f'postgresql+psycopg2://{user}:{pw}@{host}:{port}/bank_marketing_intelligence'
    body=dict(database_name=name,sqlalchemy_uri=uri,expose_in_sqllab=True,allow_ctas=False,
       allow_cvas=False,allow_dml=False,allow_file_upload=False,
       extra=json.dumps({'metadata_params':{},'engine_params':{},'bank_project':MARKER}),uuid=identity)
    if existing:
        dbid=existing[0]['id'];api.request('PUT',f'database/{dbid}',json=body)
    else:dbid=api.request('POST','database/',json=body)['id']
    identity=uid('dataset:contacts');matches=[d for d in api.all('dataset') if d['uuid']==identity]
    if matches:
        ds=matches[0]['id'];detail=api.request('GET',f'dataset/{ds}')['result']
        if not (detail.get('description') or '').startswith(MARKER):raise RuntimeError('Dataset ownership mismatch')
        api.request('PUT',f'dataset/{ds}/refresh',json={})
    else:ds=api.request('POST','dataset/',json=dict(database=dbid,schema='analytics',table_name='fact_contact',uuid=identity))['id']
    detail=api.request('GET',f'dataset/{ds}')['result'];old={m['metric_name']:m['id'] for m in detail['metrics']}
    metrics=[dict(metric_name=k,verbose_name=v[0],expression=v[1],d3format=v[2],
       description='Record grain; definition: docs/data-contract.md',**({'id':old[k]} if k in old else {})) for k,v in METRICS.items()]
    columns=[dict(id=c['id'],column_name=c['column_name'],verbose_name=LABELS.get(c['column_name'],c['column_name'])) for c in detail['columns']]
    api.request('PUT',f'dataset/{ds}',json=dict(description=MARKER+'; UCI bank-full.csv; one record per source row; no unique customer or year',
       filter_select_enabled=True,metrics=metrics,columns=columns))
    charts={}
    for item in visuals():
        f=form(item,ds)
        charts[item['key']]=api.upsert('chart',item['key'],dict(slice_name=item['title'],description=MARKER+'; '+next(p['note'] for p in PAGES if any(item in row for row in p['rows'])),
          datasource_id=ds,datasource_type='table',viz_type=f['viz_type'],params=json.dumps(f,ensure_ascii=False),query_context=json.dumps(context(item,ds),ensure_ascii=False)))
    meta=dict(native_filter_configuration=filters(ds,charts),filter_bar_orientation='HORIZONTAL',cross_filters_enabled=False,
       chart_configuration={},color_scheme='supersetColors',label_colors={k:TEAL if k=='conversion' else BLUE for k in METRICS},
       refresh_frequency=0,expanded_slices={},timed_refresh_immune_slices=[],map_label_colors={},shared_label_colors=[],color_scheme_domain=[])
    css='''
.dashboard-content,.dashboard-component-tabs-content{background:#F4F7FA;}
.dashboard-component-chart-holder{border-radius:12px;background:#FFF;border:1px solid #DCE4EB;}
.dashboard-chart{background:transparent!important;border:0!important;}
.dashboard-component-chart-holder .chart-slice{background:transparent;border:0;box-shadow:none;}
.dashboard-component-chart-holder .header-title a,.dashboard-header .editable-title{color:#183153!important;}
.dashboard-component-chart-holder .header-title a{font-size:13px!important;font-weight:600;}
.dashboard-component-tabs .ant-tabs-tab-active .ant-tabs-tab-btn{color:#168C92!important;}
.dashboard-component-tabs .ant-tabs-ink-bar{background:#168C92!important;}
.dashboard-markdown{color:#52677F;font-size:12px;line-height:18px;}
'''
    body=dict(dashboard_title=name,slug=SLUG,published=True,position_json=json.dumps(layout(charts),ensure_ascii=False),json_metadata=json.dumps(meta,ensure_ascii=False),css=css)
    light=[t for t in api.all('theme') if t.get('theme_name')=='THEME_DEFAULT' and t.get('is_system')]
    if light:body['theme_id']=light[0]['id']
    if any(d.get('slug')==SLUG and d.get('uuid')!=uid('dashboard:main') for d in api.all('dashboard')):raise RuntimeError('Unowned slug collision')
    dashboard=api.upsert('dashboard','main',body)
    for item in visuals():
        ident=charts[item['key']];f=form(item,ds);f.update(slice_id=ident,dashboards=[dashboard])
        ctx=context(item,ds);ctx['form_data']=f
        api.request('PUT',f'chart/{ident}',json=dict(dashboards=[dashboard],params=json.dumps(f,ensure_ascii=False),query_context=json.dumps(ctx,ensure_ascii=False)))
    result=dict(database_id=dbid,dataset_id=ds,charts=charts,dashboard_id=dashboard,
       dashboard_url=api.base+'/superset/dashboard/'+SLUG+'/',source='https://archive.ics.uci.edu/dataset/222/bank+marketing',
       palette=dict(navy=NAVY,teal=TEAL,blue=BLUE,amber=AMBER),pages=[p['title'] for p in PAGES])
    save('deployment.json',result)
    print(json.dumps({'url':result['dashboard_url'],'charts':len(charts),'dataset_id':ds},ensure_ascii=False))
    return result
