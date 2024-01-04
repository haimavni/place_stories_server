n_bad_hits = db(db.TblPageHits.item_id==0).delete()
hits = db((db.TblPageHits.what=="EVENT")&(db.TblPageHits.story_id==None)&(db.TblPageHits.date!=None)).select(orderby=~db.TblPageHits.id)

bad = []
total_miss = []
hits = [] ############### temp
for hit in hits:
    event = db(db.TblEvents.story_id==hit.item_id).select().first()
    if event:
        hit.update_record(story_id=event.story_id, item_id=event.id)
    else:
        bad += [hit]
        event = db(db.TblEvents.id==hit.item_id).select().first()
        if event:
            hit.update_record(story_id=event.story_id)
        else:
            total_miss += [hit]

dfukim = []
for hit in total_miss:
    story = db(db.TblStories.id==hit.item_id).select(db.TblStories.name, db.TblStories.used_for).first()
    dfukim += [story]

not_stories = []
missing = []
old_hits = db((db.TblPageHits.what=="EVENT")&(db.TblPageHits.story_id==None)&(db.TblPageHits.date==None)).select(orderby=~db.TblPageHits.id)
for hit in old_hits:
    event = db(db.TblEvents.story_id==hit.item_id).select().first()
    if event:
        continue
    story = db(db.TblStories.id==hit.item_id).select(db.TblStories.name, db.TblStories.used_for).first()
    if not story:
        missing += [hit]
    elif story.used_for!=STORY4EVENT:
        not_stories += [story]

    
