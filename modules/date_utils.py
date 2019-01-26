# -*- coding: utf-8 -*-

import datetime
from gluon.storage import Storage
from injections import inject

DATE_STR_SUFFIX = "_datestr" #todo: obsolete soon
DATE_SPAN_SUFFIX = "_datespan"
DATE_UNIT_SUFFIX = "_dateunit"
DATE_END_SUFFIX = "_dateend"

def parse_date(date_str):
    date_str = date_str.replace('.', '/').replace('-', '/')
    if date_str:
        parts = date_str.split('/')
    else:
        parts = []
    unit = 'NYMD'[len(parts)]
    parts.reverse() #we want it ymd
    parts = [int(p or 1) for p in parts]
    parts += [1, 1, 1]
    return unit, datetime.date(year=parts[0], month=parts[1], day=parts[2])

def get_all_dates(rec):
    date_formats = dict(
        Y='%Y',
        M='%m.%Y',
        D='%d.%m.%Y'
    )
    result = Storage()
    for fld_name in rec:
        if fld_name.endswith(DATE_UNIT_SUFFIX):
            unit = rec[fld_name]
            fld = fld_name[:-len(DATE_UNIT_SUFFIX)]
            date = rec[fld]
            if not date:
                unit = "N"
            date_str = ""
            if unit != 'N':
                if date.year < 1900: #strftime does not accept dates before 1900
                    year = date.year
                    date = datetime.date(year=1900, month=date.month, day=date.day)
                else:
                    year = 0
                date_str = date.strftime(date_formats[unit])
                if year:
                    date_str = date_str.replace('1900', str(year))
            fld_span = fld + DATE_SPAN_SUFFIX
            item = Storage(
                date=date_str,
                span=rec[fld_span]
            )
            result[fld] = item
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

def fix_record_dates_out(rec):
    all_dates = get_all_dates(rec)
    for fld in all_dates:
        rec[fld + DATE_STR_SUFFIX] = all_dates[fld].date
        rec[fld + DATE_SPAN_SUFFIX] = all_dates[fld].span
        
def fix_record_dates_in(rec, data):
    result = dict()
    date_fields = set([])
    for fld_name in rec:
        if fld_name.endswith(DATE_UNIT_SUFFIX):
            date_fld = fld_name[:-len(DATE_UNIT_SUFFIX)]
            span_fld = date_fld + DATE_SPAN_SUFFIX
            date_fields |= set([fld_name, date_fld, span_fld])
    for fld_name in rec:
        if fld_name in date_fields:
            if fld_name.endswith(DATE_UNIT_SUFFIX):
                date_fld = fld_name[:-len(DATE_UNIT_SUFFIX)]
                date_str_fld = date_fld + DATE_STR_SUFFIX
                if date_str_fld not in data:
                    continue
                date_str = data[date_str_fld]
                date_unit, date = parse_date(date_str)
                result[fld_name] = date_unit  #unit
                result[date_fld] = date       #base date
                span_fld = date_fld + DATE_SPAN_SUFFIX
                result[span_fld] = data[span_fld]
        elif fld_name in data:
            result[fld_name] = data[fld_name]
    return result

def calc_date_end(date, unit, span):
    if unit == 'Y':
        return datetime.date(year=date.year + span, month=1, day=1)
    elif unit == 'M':
        m = date.month + span - 1
        year = date.year + m / 12
        month = m % 12 + 1
        return datetime.date(year=year, month=month, day=1)
    elif unit == 'D':
        td = datetime.timedelta(days = span)
        return date + td
    else:
        raise Exception('date has no unit')
            
def update_record_dates(rec, dates_info):
    data = dict()
    for date_fld in dates_info:
        date_str, date_span = dates_info[date_fld]
        date_unit, date = parse_date(date_str)
        data[date_fld] = date
        data[date_fld + DATE_SPAN_SUFFIX] = date_span
        data[date_fld + DATE_UNIT_SUFFIX] = date_unit
        date_end = calc_date_end(date, date_unit, date_span)
        data[date_fld + DATE_END_SUFFIX] = date_end
    rec.update_record(**data)

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

def fix_all_date_ends():
    db, NO_DATE = inject('db', 'NO_DATE')
    for tbl in [db.TblEvents, db.TblMembers, db.TblPhotos, db.TblVideos, db.TblDocs]:
        try:
            for rec in db(tbl.deleted != True).select():
                data = dict()
                for fld in tbl.fields():
                    if not fld.endswith(DATE_SPAN_SUFFIX):
                        continue
                    fld_date = tbl[fld].name[:-len(DATE_SPAN_SUFFIX)]
                    date = rec[fld_date] or NO_DATE
                    suf = rec[fld_date + DATE_UNIT_SUFFIX] or 'Y'
                    if suf == 'N':
                        data[fld_date + DATE_UNIT_SUFFIX] = 'Y'
                        suf = 'Y'
                    span = rec[fld_date + DATE_SPAN_SUFFIX] or 1
                    date_end = calc_date_end(date, suf, span)
                    data[fld_date + DATE_END_SUFFIX] = date_end
                rec.update_record(**data)
            db.commit()
        except Exception, e:
            print e
    return 'All date ends fixed'
    
if __name__ == '__main__'    :
    test()
 