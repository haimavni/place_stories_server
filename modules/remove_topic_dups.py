from .injections import inject

def make_item_topics_unique(topic_id):
    db, request = inject('db', 'request')
    lst = db(db.TblItemTopics.topic_id==topic_id).select()
    dic = dict()
    for rec in lst:
        if rec.story_id not in dic:
            dic[rec.story_id] = []
        dic[rec.story_id] = dic[rec.story_id] + [rec.id]
    ndups = 0
    for story_id in dic:
        lst1 = dic[story_id][1:]
        for id in lst1:
            ndups += 1
            if request.vars.clean:
                db(db.TblItemTopics.id==id).delete()
    return ndups

def make_all_item_topics_unique():
    db, log_path = inject('db', 'log_path')
    topics = db(db.TblTopics).select()
    dups = []
    path = log_path() + 'duplicate_topic_stories.log'
    with open(path, 'w') as f:
        for topic in topics:
            ndups = make_item_topics_unique(topic.id)
            if ndups > 0:
                s = '{} {} had {} dups\n'.format(topic.id, topic.name, ndups)
                f.write(s)
                dups.append(s)
    return dups or "No duplicates found"