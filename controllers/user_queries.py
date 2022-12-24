'''
This controller supports user-generated queries into the db.
Fields for which specific attributes are defined can be used.
Only these attributes are used in order to generate the UI
and usage of the queries
'''
from date_utils import parse_date

@serve_json
def available_fields(vars):
    table = db[vars.table_name]
    field_list = []
    fields = []
    field_names = table.fields()
    for field_name in field_names:
        field = table[field_name]
        if field_name != 'id' and not hasattr(field, 'description'):
            continue
        rec = dict(
            name=field.name,
            type=field.type,
            description=getattr(field, 'description')
        )
        if hasattr(field, 'options'):
            rec['options'] = getattr(field, 'options')
        field_list.append(rec)
    if vars.record_id:
        #place current_value in field_list
        vmap = get_current_values(table, fields, vars.record_id)
        for field in field_list:
            field.current_value = vmap[field.name]
    return dict(field_list=field_list)

@serve_json
def do_query(vars):
    table_name = vars.table_name
    table = db[table_name]
    fields = vars.fields
    field = table['deleted']
    query = field != True
    for fld in fields:
        q = make_query(table, fld.field_name, fld.op, fld.value)
        query &= q
    if vars.negative:
        query = ~query
    lst = db(query).select()
    lst = [rec.id for rec in lst]
    lst = sorted(lst)
    return dict(selected_ids=lst)

def make_query(table, field_name, op=None, value=None):
    field = table[field_name]
    if isinstance(value, list):
        return (field.belongs(value))
    # todo: use match once in python 3.10 or later
    if field.type == 'date':
        date_unit, value = parse_date(value)
    if op == "<":
        return field < value
    if op == "<=":
        return field <= value
    if op == "==":
        return field == value
    if op == "!=":
        return field != value
    if op == ">":
        return field > value
    if op == ">=":
        return field >= value
    raise Exception(f"Unknown operator {op}")

def get_current_values(table, fields, record_id):
    rec = db(table.id==record_id).select(*fields).first()
    result = dict()
    for field_name in rec:
        result[field_name] = rec[field_name]
    return result
