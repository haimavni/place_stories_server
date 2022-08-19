bios = db((db.TblStories.used_for==STORY4MEMBER)&(db.TblStories.deleted!=True)).select(db.TblStories.id)
bad_list = []
for bio in bios:
    mc = db(db.TblMembers.story_id==bio.id).count()
    if mc == 0:
        bad_list.append(bio.id)
bio = None
bios = None
member = None
detached_bios = db(db.TblStories.id.belongs(bad_list)).select(db.TblStories.id,db.TblStories.preview)
fixers = dict()
obs = [411,412,414,415,423,431,398]
obs = []
#fixers[171] = 397
#fixers[175] = 399
#fixers[177] = 413
for k in fixers:
    db(db.TblMembers.id==k).update(story_id=fixers[k])
for i in obs:
    db(db.TblStories.id==i).update(deleted=True)
mc = None
obs = None
fixers = None
detached_bios = None
