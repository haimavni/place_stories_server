import datetime
import stories_manager
from words import get_reisha

def init_previews():
    time_budget = request.vars.time_budget or 180
    time_budget = int(time_budget)
    t0 = datetime.datetime.now()
    q = (db.TblStories.deleted != True) & (db.TblStories.preview==None)
    while True:
        lst = db(q).select(db.TblStories.id, db.TblStories.preview, db.TblStories.story, limitby=(0, 100))
        if not lst:
            break
        for rec in lst:
            sm = stories_manager.Stories()
            story = sm.get_story(rec.id)
            if story.story_text:
                preview = get_reisha(story.story_text)
            else:
                preview = ''
            rec.update_record(preview=preview)
            
        db.commit()
        dif = datetime.datetime.now() - t0
        elapsed = int(dif.total_seconds())
        if elapsed > time_budget:
            break
    return "{} stories remain".format(db(q).count())