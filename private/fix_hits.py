def fix_hit_records():
    db, STORY4EVENT, STORY4TERM, STORY4MEMBERS = ('db', 'STORY4EVENT', 'STORY4TERM', 'STORY4MEMBERS')
    n_bad_hits = db(db.TblPageHits.item_id==0).delete()
    hits = db((db.TblPageHits.what=="EVENT")&(db.TblPageHits.story_id==None)&(db.TblPageHits.date!=None)).select(orderby=~db.TblPageHits.id)

    bad = []
    total_miss = []
    for hit in hits:
        event = db(db.TblEvents.story_id==hit.item_id).select().first()
        if event:
            hit.update_record(story_id=event.story_id, item_id=event.id)
        else:
            story = db(db.TblStories.id==hit.item_id).select(db.TblStories.name, db.TblStories.used_for).first()
            bad += [dict(hit=hit, story=story)]
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
    found_events = []
    old_hits = db((db.TblPageHits.what=="EVENT")&(db.TblPageHits.story_id==None)&(db.TblPageHits.date==None)).select(orderby=~db.TblPageHits.id)
    for hit in old_hits:
        event = db(db.TblEvents.story_id==hit.item_id).select().first()
        if event:
            item_id = hit.item_id
            found_events += [hit]
            hit.update_record(story_id=item_id, item_id=event.id)
            continue
        story = db(db.TblStories.id==hit.item_id).select(db.TblStories.name, db.TblStories.used_for).first()
        if not story:
            missing += [hit]
        elif story.used_for!=STORY4EVENT:
            not_stories += [dict(hit=hit, story=story)]
            if story.used_for==STORY4MEMBER:
                member = db(db.TblMembers.story_id == hit.item_id).select().first()
                if member:
                    hit.update_record(what="MEMBER", item_id=member.id, story_id=hit.item_id)
            elif story.used_for==STORY4TERM:
                term = db(db.TblTerms.story_id==hit.item_id).select().first()
                if term:
                    hit.update_record(what="TERM", story_id=hit.item_id, item_id=term.id) 
    return dict(bad=bad, total_miss=total_miss, dfukim=dfukim, missing=missing, not_stories=not_stories)
