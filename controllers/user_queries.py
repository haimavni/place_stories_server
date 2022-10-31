'''
This controller supports user-generated queries into the db.
Fields for which specific attributes are defined can be used.
Only these attributes are used in order to generate the UI
and usage of the queries
'''

@serve_json
def available_fields(vars):
    table = db[vars.table]
    field_list = []
    for fld in table.fields():
        if not hasattr(fld, 'description'):
            continue
        rec = dict(
            type = fld.type,
            description = fld.description
        )
        field_list.append(rec)
    return dict(field_list=field_list)

@serve_json
def do_query(vars):
    table_name = table_name
    query = None
    for fld in vars.fields:
        q = make_query(table_name, fld.field_name, fld.op, fld.value)
        if query:
            query &= q
        else:
            query = q
    lst = db(query).select()
    lst = [rec.id for rec in lst]
    return dict(selected_ids=lst)

def make_query(table_name, field_name, op=None, value=None):
    field = db[table_name][field_name]
    if isinstance(value, list):
        return (field.belongs(value))
    # todo: use match once in python 3.10 or later
    if op == "==":
        return field == value
    if op == "<":
        return field < value
    if op == "<=":
        return field <= value
    if op == ">":
        return field > value
    if op == ">=":
        return field >= value
    raise Exception(f"Unknown operator {op}")
