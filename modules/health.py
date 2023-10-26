from .injections import inject
from folders import local_photos_folder
from gluon.storage import Storage
import os
from folders import RESIZED, ORIG, SQUARES, PROFILE_PHOTOS


def verify_topic_types(typ):
    db = inject('db')
    usage_of_char = {'E': 2, 'P': 3, 'T': 4, 'V': 8, 'D': 9, 'A': 10, 'S': 14}
    usage = usage_of_char[typ]
    vtopics = db(db.TblTopics.usage.like(f"%{typ}%")).select()
    topic_ids = db((db.TblStories.used_for == usage) &
                   (db.TblStories.deleted != True) &
                   (db.TblTopics.id == db.TblItemTopics.topic_id) &
                   (db.TblTopics.topic_kind == 2) &
                   (db.TblItemTopics.story_id == db.TblStories.id)).select(db.TblItemTopics.topic_id)

    topic_set = set([a.topic_id for a in topic_ids])

    bad_topics = [top for top in vtopics \
                  if top.topic_kind ==  2 and top.id not in topic_set]

    result = []
    for trec in db(db.TblTopics.id.belongs(bad_topics)).select():
        result.append(trec)
        usage = trec.usage.replace(typ, '')
        trec.update_record(usage=usage)
    return dict(result=result, bad_topics=bad_topics)


def verify_all_topic_types():
    bad_topics = []
    for typ in 'EPTVDAS':
        result = verify_topic_types(typ)
        if result['bad_topics']:
            bad_topics.append(result)
    return bad_topics


def check_detached_member_stories():
    db = inject('db')
    detached_member_stories = []
    for srec in db((db.TblStories.used_for == 1) & (db.TblStories.deleted != True)).select(db.TblStories.id):
        mrec = db(db.TblMembers.story_id == srec.id).select().first()
        if (not mrec) or mrec.deleted:
            detached_member_stories.append(dict(story_id=srec.id, story_name=srec.name))
            srec.update_record(deleted=True)
    return detached_member_stories


def check_missing_photos():
    db = inject('db')
    missing = []
    good = 0
    for prec in db(db.TblPhotos.deleted != True).select():
        photo_path = local_photos_folder(RESIZED) + prec.photo_path
        if not os.path.exists(photo_path):
            item = Storage(pid=prec.id, photo_path=photo_path)
            over_path = local_photos_folder(ORIG) + prec.photo_path
            if os.path.exists(over_path):
                item.has_copy = True
            missing.append(item)
        else:
            good += 1
    return dict(missing=missing, good=good)


def check_health():
    bad_topics = verify_all_topic_types()
    detached_member_stories = check_detached_member_stories()
    missing = check_missing_photos()
    return dict(topic_issues=bad_topics,
                detached_member_stories=detached_member_stories,
                missing_photos=missing
                )
    
def misplaced_photos():
    db = inject("db")
    lst = db(db.TblPhotos.photo_path.like("%uploads%")).select(db.TblPhotos.id,db.TblPhotos.photo_path,db.TblPhotos.name,orderby=db.TblPhotos.id)
    misplaced_top = []
    for r in lst:
        if r.photo_path[7] != "/":
            misplaced_top.append(r)
    lst = db(db.TblPhotos.photo_path.like("%202%-%")).select(db.TblPhotos.id,db.TblPhotos.photo_path,db.TblPhotos.name,orderby=db.TblPhotos.id)
    misplaced_year = []
    for r in lst:
        if r.photo_path[15] != "/":
            misplaced_year.append(r)
    return dict(misplaced_top=misplaced_top, misplaced_year=misplaced_year)