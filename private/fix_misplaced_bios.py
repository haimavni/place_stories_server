from stories_manager import Stories

def make_photo_story(name):
    sm = Stories()
    story_info = sm.get_empty_story(used_for=STORY4PHOTO, story_text="", name=name)
    result = sm.add_story(story_info)
    return result.story_id

lst = [(76, 297), (31, 289)]#,(201,295),(200,294),(199,293),(198,291),(187,292),(196,290),(195,287),(194,286),(193,285),(192,281),(191,282)]    
for elem in lst:
    mem_id, photo_id = elem
    photo_rec = db(db.TblPhotos.id==photo_id).select().first()
    story_id = photo_rec.story_id
    story_rec = db(db.TblStories.id==story_id).select().first()
    story_rec.update_record(used_for=STORY4MEMBER)
    member_rec = db(db.TblMembers.id==mem_id).select().first()
    member_rec.update_record(story_id=story_id)
    photo_story_id = make_photo_story(photo_rec.name)
    photo_rec.update_record(story_id=photo_story_id)