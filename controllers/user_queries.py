'''
This controller supports user-generated queries into the db.
Fields for which specific attributes are defined can be used.
Only these attributes are used in order to generate the UI
and usage of the queries
'''
from date_utils import parse_date

def comment(s):
    with open('/apps_data/gbs/logs/comments.log', 'a', encoding='utf-8') as f:
        f.write(str(s) + '\n')

@serve_json
def available_fields(vars):
    table = db[vars.table_name]
    field_list = []
    field_names = table.fields()
    for field_name in field_names:
        field = table[field_name]
        if not hasattr(field, 'description'):
            continue
        rec = dict(
            name=field.name,
            type=field.type,
            description=field.description
        )
        if hasattr(field, 'values'):
            rec['values'] = field.values
        field_list.append(rec)
    return dict(field_list=field_list)

@serve_json
def do_query(vars):
    drek = str(vars.__class__)
    comment(f"drek: {drek}")
    table_name = vars.table_name
    comment(f"table name: {table_name}")
    fields = vars.fields
    query = None
    for fld in fields:
        q = make_query(table_name, fld.field_name, fld.op, fld.value)
        if query:
            query &= q
        else:
            query = q
    if vars.negative:
        query = ~query
    lst = db(query).select()
    lst = [rec.id for rec in lst]
    lst = sorted(lst)
    return dict(selected_ids=lst)

def make_query(table_name, field_name, op=None, value=None):
    comment(f"table name: {table_name} field_name: {field_name}")
    field = db[table_name][field_name]
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
