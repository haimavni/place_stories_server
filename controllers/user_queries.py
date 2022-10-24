'''
This controller supports user-generated queries into the db.
Fields for which specific attributes are defined can be used.Only these attributes are used in order to generate the UI
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
            type = fld.type
            description = fld.description
        )
        field_list.append(rec)
    return dict(field_list=field_list)