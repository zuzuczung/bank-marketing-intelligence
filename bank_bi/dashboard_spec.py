"""One fact grain; every filter recomputes weighted rates from raw counts."""
NAVY='#35204F'; TEAL='#7C3AED'; BLUE='#9D7BD8'; AMBER='#B79AD9'
P='SUM(subscribed)::numeric/NULLIF(COUNT(*),0)'
N='NULLIF(COUNT(*),0)::numeric'
C=f'(({P})+3.8416/(2*({N})))'
E=f'(1.96*SQRT(({P})*(1-({P}))/({N})+3.8416/(4*({N})^2)))'
D=f'(1+3.8416/({N}))'
METRICS={
 'records':('Bản ghi','COUNT(*)',',d'),
 'subscribers':('Đăng ký','COALESCE(SUM(subscribed),0)',',d'),
 'conversion':('Tỷ lệ đăng ký',P,'.1%'),
 'avg_contacts':('Lần liên hệ TB','AVG(campaign_contacts)','.2f'),
 'prior_records':('Bản ghi từng được liên hệ','COUNT(*) FILTER(WHERE previously_contacted)',',d'),
 'ci_low':('Wilson 95% · dưới',f'({C}-{E})/{D}','.1%'),
 'ci_high':('Wilson 95% · trên',f'({C}+{E})/{D}','.1%'),
}
LABELS={'source_row':'Dòng nguồn','age':'Tuổi','age_band':'Nhóm tuổi','job':'Nghề nghiệp',
 'education':'Học vấn','contact_label':'Kênh liên hệ','month_label':'Tháng lịch (gộp năm)',
 'contact_band':'Số lần liên hệ trong chiến dịch','previous_outcome_label':'Kết quả chiến dịch trước',
 'campaign_contacts':'Số lần liên hệ','subscribed':'Đăng ký (0/1)'}


def v(key,title,kind,metric,dimension=None,**extra):
    return dict(key=key,title=title,kind=kind,metric=metric,dimension=dimension,**extra)


PAGES=[
 dict(key='overview',title='Tổng quan',note='UCI Bank Marketing · 45.211 bản ghi lịch sử, không phải số khách duy nhất. Tháng lịch gộp các năm vì nguồn không có năm; các bộ lọc áp dụng cho toàn dashboard.',rows=[
  [v('records','Bản ghi','kpi','records'),v('subscriptions','Đăng ký tiền gửi','kpi','subscribers'),v('conversion','Tỷ lệ đăng ký','kpi','conversion')],
  [v('channel-volume','Quy mô theo kênh','bar','records','contact_label'),v('channel-rate','Tỷ lệ đăng ký theo kênh','bar','conversion','contact_label')],
  [v('month-volume','Bản ghi theo tháng lịch (gộp năm)','bar','records','month_label',ordered=True),v('month-rate','Tỷ lệ theo tháng lịch (gộp năm)','bar','conversion','month_label',ordered=True)],
  [v('channel-detail','Kênh liên hệ: quy mô và tỷ lệ','table','records','contact_label',metrics=['records','subscribers','conversion','ci_low','ci_high'])],
 ]),
 dict(key='segments',title='Phân khúc khách hàng',note='So sánh mô tả theo bản ghi; nhóm nhỏ cần xem cả quy mô. Khoảng Wilson 95% là xấp xỉ nhị thức, không chứng minh hiệu quả nhân quả hoặc khả năng triển khai.',rows=[
  [v('job-rate','Tỷ lệ đăng ký theo nghề nghiệp','bar','conversion','job',horizontal=True,width=7),v('age-rate','Tỷ lệ đăng ký theo nhóm tuổi','bar','conversion','age_band',ordered=True,width=5)],
  [v('education-rate','Tỷ lệ đăng ký theo học vấn','bar','conversion','education',horizontal=True,width=5),v('job-detail','Nghề nghiệp: mẫu số và khoảng 95%','table','records','job',width=7,metrics=['records','subscribers','conversion','ci_low','ci_high'])],
 ]),
 dict(key='contacts',title='Liên hệ & lịch sử',note='Số lần liên hệ được ghi nhận đến cuối chiến dịch, gồm lần cuối. Chênh lệch tỷ lệ có thể do cách chọn khách và thời điểm dừng gọi; không kết luận gọi ít/nhiều làm tăng đăng ký. Chưa có chi phí để tính ROI.',rows=[
  [v('avg-contacts','Lần liên hệ TB / bản ghi','kpi','avg_contacts'),v('prior-records','Bản ghi từng được liên hệ trước','kpi','prior_records')],
  [v('contact-volume','Quy mô theo số lần liên hệ','bar','records','contact_band',ordered=True),v('contact-rate','Tỷ lệ theo số lần liên hệ','bar','conversion','contact_band',ordered=True)],
  [v('previous-rate','Tỷ lệ theo kết quả chiến dịch trước','bar','conversion','previous_outcome_label',horizontal=True,width=5),v('previous-detail','Lịch sử chiến dịch: quy mô và tỷ lệ','table','records','previous_outcome_label',width=7,metrics=['records','subscribers','conversion','ci_low','ci_high'])],
 ]),
]


def visuals():return [i for p in PAGES for r in p['rows'] for i in r]


def form(item,ds):
    kind=item['kind'];m=item['metric'];fmt=METRICS[m][2]
    viz={'kpi':'big_number_total','bar':'echarts_timeseries_bar','table':'table'}[kind]
    color=TEAL if m=='conversion' else AMBER if m=='avg_contacts' else BLUE
    f=dict(datasource=f'{ds}__table',viz_type=viz,time_range='No filter',
      metrics=item.get('metrics',[m]),adhoc_filters=[],row_limit=1000,
      order_desc=True,extra_form_data={},color_scheme='supersetColors',
      label_colors={m:color,METRICS[m][0]:color},number_format=fmt,y_axis_format=fmt,
      show_legend=False,annotation_layers=[],rich_tooltip=True,show_empty_columns=True)
    if kind=='kpi':
        f.update(metric=m,header_font_size=.32,subheader_font_size=.12)
    elif kind=='table':
        f.update(query_mode='aggregate',groupby=[item['dimension']],all_columns=[],
         percent_metrics=[],include_search=True,show_cell_bars=False,page_length=12,
         show_totals=False,order_by_cols=[],column_config={k:{'d3NumberFormat':METRICS[k][2]} for k in f['metrics']})
    else:
        dim=item['dimension']
        f.update(x_axis=dim,groupby=[],xAxisForceCategorical=True,
         x_axis_sort=dim if item.get('ordered') else m,
         x_axis_sort_asc=bool(item.get('ordered') or item.get('horizontal')),
         orientation='horizontal' if item.get('horizontal') else 'vertical',
         x_axis_title='',y_axis_title='',x_axis_title_margin=24,y_axis_title_margin=60,
         truncateXAxis=False,truncate_metric=True,show_value=True,
         xAxisLabelRotation=45 if dim=='month_label' else 30 if dim=='age_band' else 0,
         showTooltipTotal=False,zoomable=False,truncateYAxis=False)
    return f


def context(item,ds,filters=None):
    m=item['metric'];dim=item['dimension']
    query=dict(columns=[dim] if dim else [],metrics=item.get('metrics',[m]),
       filters=filters or [],time_range='No filter',extras={'having':'','where':''},
       row_limit=1000,orderby=[(m,False)] if dim else [],order_desc=True,
       applied_time_extras={})
    return dict(datasource={'id':ds,'type':'table'},force=True,queries=[query],form_data=form(item,ds),result_format='json',result_type='full')
