# -*- coding: utf-8 -*-

import datetime

DATE_STR_SUFFIX = "_datestr"
DATE_SPAN_SUFFIX = "_daterange"

def parse_date(date_str):
    if date_str:
        parts = date_str.split('/')
    else:
        parts = []
    kind = 'NYMD'[len(parts)]
    parts.reverse() #we want it ymd
    parts = [int(p or 1) for p in parts]
    parts += [1, 1, 1]
    return kind, datetime.date(year=parts[0], month=parts[1], day=parts[2])

def get_all_dates(rec):
    result = ''
    for fld_str in rec:
        if fld_str.endswith(DATE_STR_SUFFIX):
            fld = fld_str[:-len(DATE_STR_SUFFIX)]
            fld_range = fld + DATE_SPAN_SUFFIX
            item = dict(
                date=rec[fld_str],
                span=rec[fld_range]
            )
            result.append(item)
    return result

def date_of_date_str(date_str):
    if not date_str:
        date_str = '????-??-??'
    date_str = date_str.replace('/', '-').replace('.', '-')
    lst = (date_str + '-??-??').split('-')[:3]
    d = 1
    m = 1
    y = 1
    ys, ms, ds = lst
    if len(ds) == 4:  #date is dd/mm/yyyy
        ds, ms, ys = lst
    date_str = '{}-{}-{}'.format(ys, ms, ds)
    if ys.startswith('?'):
        return date_str, datetime.date(day=d, month=m, year=y)
    if ys.endswith('?'):
        ys = ys[0:3] + '0'
        year = int(ys)
        return date_str, datetime.date(day=d, month=m, year=y)
    y = int(ys)
    if ms == '??':
        return date_str, datetime.date(day=d, month=m, year=y)
    m = int(ms)
    if ds == '??':
        return date_str, datetime.date(day=d, month=m, year=y)
    d = int(ds)
    return date_str, datetime.date(day=d, month=m, year=y)

def string_date_to_date(s):
    p = "שנות ה"
    day = 1
    mon = 1
    year = 1
    raw_str = '????-??-??'
    if s:
        s = s.replace(' ', '')
        m = re.search(r'(\d{4})\-(\d{4})', s)
        if m:
            return ('lifespan', m.group(1), m.group(2))
        if p in s:
            m = re.search(r'(\d{1,2})', s)
            if m:
                year = m.groups()[0]
                if len(year) < 2:
                    year += '0'
                year = 1900 + int(year)
                raw_str = str(year) + '-??-??'
        else:
            m = re.search(r'(\d{1,2})[./-](\d{1,2})[./-](\d{4})', s)
            if m:
                day, mon, year = m.groups()
                day, mon, year = (int(day), int(mon), int(year))
                raw_str = '{year:04}-{mon:02}-{day:02}'.format(year=year, mon=mon, day=day)
            else:
                m = re.search(r'(\d{1,2})[./-](\d{4})', s)
                if m:
                    mon, year = m.groups()
                    mon, year = (int(mon), int(year))
                    raw_str = '{year:04}-{mon:02}-??'.format(year=year, mon=mon)
                else:
                    m = re.search(r'(\d{4})', s)
                    if m:
                        year = int(m.groups()[0])
                        raw_str = '{year:04}-??-??'.format(year=year)

    return ('singledate', datetime.date(year=year, month=mon, day=day), raw_str)

def test():
    s = '2016-04-15'
    print date_of_date_str(s)
    s = '2017-??-??'
    print date_of_date_str(s)
    for s in ['', '1945', '08/1945', '25/8/1945']:
        print parse_date(s)
        
def datetime_from_str(s, date_only=False):
    date, time = s.split(' ')
    parts = date.split(':')
    y, m, d = [int(p) for p in parts]
    if date_only:
        return datetime.date(year=y, month=m, day=d)
    parts = time.split(':')
    h,mn,s = [int(p) for p in parts]
    return datetime.datetime(year=y, month=m, day=d, hour=h, minute=mn, second=s)
    
if __name__ == '__main__'    :
    test()
    

    


