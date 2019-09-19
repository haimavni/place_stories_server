def del_stories_of_deleted_photos():
    qq = (db.TblPhotos.story_id==db.TblStories.id) & (db.TblPhotos.deleted>db.TblStories.deleted)
    lst = db(qq).select()
    lst1 = [rec.TblStories.id for rec in lst]
    db(db.TblStories.id.belongs(lst1)).update(deleted = True)