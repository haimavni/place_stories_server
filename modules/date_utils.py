# -*- coding: utf-8 -*-

import datetime

def date_of_date_str(date_str):
    if not date_str:
        return None
    d = 1
    m = 1
    y = 1
    ys, ms, ds = date_str.split('-')
    if ys.startswith('?'):
        return datetime.date(day=d, month=m, year=y)
    if ys.endswith('?'):
        ys = ys[0:3] + '0'
        year = int(ys)
        return datetime.date(day=d, month=m, year=y)
    y = int(ys)
    if ms == '??':
        return datetime.date(day=d, month=m, year=y)
    m = int(ms)
    if ds == '??':
        return datetime.date(day=d, month=m, year=y)
    d = int(ds)
    return datetime.date(day=d, month=m, year=y)

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
    
if __name__ == '__main__'    :
    test()
    

    

