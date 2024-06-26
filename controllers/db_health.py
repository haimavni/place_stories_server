def remove_detached_member_stories():
    lst = db(db.TblStories.used_for==STORY4MEMBER).select(db.TblStories.id)
    lst = [rec.id for rec in lst]
    detached = 0
    for sid in lst:
        if db(db.TblMembers.story_id==sid).count() == 0:
            comment(f'story #{sid} is detached')
            detached += 1
            db(db.TblStories.id==sid).update(deleted=True)
    return f'{detached} detached stories found'
