"""Source contracts and independent Python segment definitions."""
from .source import COLUMNS, MONTHS

DOMAINS = {
 'job':{'admin.','blue-collar','entrepreneur','housemaid','management','retired',
        'self-employed','services','student','technician','unemployed','unknown'},
 'marital':{'divorced','married','single'},
 'education':{'unknown','primary','secondary','tertiary'},
 'default':{'yes','no'}, 'housing':{'yes','no'}, 'loan':{'yes','no'},
 'contact':{'unknown','telephone','cellular'}, 'month':set(MONTHS),
 'poutcome':{'unknown','other','failure','success'}, 'y':{'yes','no'}
}


def validate_row(row):
    if set(row)!=set(COLUMNS) or any(v is None or not v.strip() for v in row.values()):
        raise ValueError('Missing field or blank source cell')
    for col, values in DOMAINS.items():
        if row[col].strip().lower() not in values:
            raise ValueError('Unexpected categorical value: '+col)
    ints={c:int(row[c]) for c in ['age','balance','day','duration','campaign','pdays','previous']}
    if not (ints['age']>0 and 1<=ints['day']<=31 and ints['duration']>=0
            and ints['campaign']>=1 and ints['pdays']>=-1 and ints['previous']>=0):
        raise ValueError('Numeric range violation')
    return True


def age_band(age):
    for edge,label in [(30,'01 · Dưới 30'),(40,'02 · 30–39'),(50,'03 · 40–49'),(60,'04 · 50–59')]:
        if age<edge:return label
    return '05 · Từ 60'


def contact_band(n):
    for edge,label in [(1,'01 · 1 lần'),(2,'02 · 2 lần'),(3,'03 · 3 lần'),
                       (5,'04 · 4–5 lần'),(10,'05 · 6–10 lần')]:
        if n<=edge:return label
    return '06 · Trên 10 lần'


def dimension(row, col):
    if col=='age_band':return age_band(int(row['age']))
    if col=='contact_band':return contact_band(int(row['campaign']))
    if col=='contact_label':return {'cellular':'Di động','telephone':'Điện thoại bàn','unknown':'Chưa rõ'}[row['contact']]
    if col=='previous_outcome_label':return {'success':'Thành công','failure':'Thất bại','other':'Khác','unknown':'Chưa rõ'}[row['poutcome']]
    if col=='month_label':
        n=MONTHS.index(row['month'])+1
        return f'{n:02d} · Tháng {n}'
    return row[col]
