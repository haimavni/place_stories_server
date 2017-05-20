import re
from gluon.validators import Validator
from datetime import datetime

def insert_or_update(tbl, **data_fields):
    rec_id = data_fields.get('id', None)
    errors = {}
    fields = [field for field in tbl.fields()]
    uf = dict()
    for fld in fields:
        if fld in data_fields:
            field = tbl[fld]
            db = field.db
            value = data_fields[fld]
            value, error = field.validate(value)
            if isinstance(error, dict):
                for f in error:
                    uf[f] = error[f]
                error = None
            if error:
                errors[fld] = error
            uf[fld] = value
    if errors:
        return dict(errors=errors)
    if rec_id:
        db(tbl.id==rec_id).update(**uf)
    else:
        rec_id = tbl.insert(**uf)
    return rec_id

class IS_FUZZY_DATE(Validator):
    
    def __call__(self, value):
        if not value:
            return (value, None)
        lst = re.split(r'[-/.]', value)
        try:
            lst = [int(s) for s in lst]
        except:
            return (value, 'Numbers are excpected')
        if len(lst) == 1:
            y = lst[0] + 2000
            m = 1
            d = 1
        elif len(lst) == 2:
            m, y = lst
            y += 1000
            d = 1
        elif len(lst) == 3:
            if lst[0] > 1000:
                y, m, d = lst
            elif lst[2] > 1000:
                d, m, y = lst
            else:
                return (value, 'Year must have 4 digits')
        else:
            return (value, 'Illegal date')
        try:
            date = datetime(year=y, month=m, day=d)
        except Exception, e:
            return (value, e.message)
        date = datetime.date(date)
        return (str(date), None)

def represent_fuzzy_date(value):
    if not value:
        return ''
    y, m, d = value.year, value.month, value.day
    if y > 3500:
        s = str(y - 2000)
    elif y > 2500:
        s = '{}/{}'.format(m, y - 1000)
    else:
        s = '{}/{}/{}'.format(d, m, y)
    return s
