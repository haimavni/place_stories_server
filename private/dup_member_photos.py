cmd = """
    SELECT "TblMemberPhotos"."Member_id", "TblMemberPhotos"."Photo_id", count("TblMemberPhotos"."id")
    FROM "TblMemberPhotos"
    GROUP BY "TblMemberPhotos"."Member_id", "TblMemberPhotos"."Photo_id";
"""

lst = db.executesql(cmd)

lst1 = []

for x in lst:
    if x[2] > 1:
        y = Storage(member=x[0], photo=x[1])
        lst1.append(y)
ndup = len(lst1)

lst = None

lst2 = []

lst3 = []
for x in lst1[:100]:
    rec = db((db.TblMemberPhotos.Member_id==x.member) & (db.TblMemberPhotos.Photo_id==x.photo) & (db.TblMemberPhotos.r==None)).select().first()
    if not rec:
        continue
    lst2.append(rec)
    lst3.append(rec.id)
    ###db(db.TblMemberPhotos.id==rec.id).delete()

ndel = db(db.TblMemberPhotos.id.belongs(lst3)).delete()

lst1 = None
rec = None
cmd = None
x = None
y = None