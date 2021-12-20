from .injections import inject


def verify_topic_types(typ):
    db = inject('db')
    usage_of_char = {'E': 2, 'P': 3, 'T': 4, 'V': 8, 'D': 9, 'A': 10}
    usage = usage_of_char[typ]
    vtopics = db(db.TblTopics.usage.like(f"%{typ}%")).select()
    topic_ids = db((db.TblStories.used_for == usage) &
                   (db.TblStories.deleted != True) &
                   (db.TblTopics.id == db.TblItemTopics.topic_id) &
                   (db.TblTopics.topic_kind == 2) &
                   (db.TblItemTopics.story_id == db.TblStories.id)).select(db.TblItemTopics.topic_id)

    topic_set = set([a.topic_id for a in topic_ids])

    bad_topics = [top for top in vtopics if top.topic_kind == 2 and top.id not in topic_set]

    result = []
    for trec in db(db.TblTopics.id.belongs(bad_topics)).select():
        result.append(trec)
        usage = trec.usage.replace(typ, '')
        trec.update_record(usage=usage)
    return dict(result=result, bad_topics=bad_topics)
