def del_stories_of_deleted_photos():
    qq = (db.TblPhotos.story_id==db.TblStories.id) & (db.TblPhotos.deleted>db.TblStories.deleted)
    lst = db(qq).select()
    lst1 = [rec.TblStories.id for rec in lst]
    db(db.TblStories.id.belongs(lst1)).update(deleted = True)

def fix_columns_case():
    dic = dict()
    tables = db.tables()
    for table in tables:
        fields = db[table].fields()
        for field in fields:
            if field == field.lower():
                continue
            if table not in dic:
                dic[table] = []
            dic[table].append(field)
    with open('/home/haim/fix_columns_case.sql', 'w') as f:
        for table in dic:
            for column in dic[table]:
                f.write(f'alter table "{table}" rename {column.lower()} to "{column}";\n')
    return "fix_columns_case.sql created in /home/haim"

