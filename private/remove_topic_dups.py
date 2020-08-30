from injections import inject

def make_item_topics_unique(topic_id):
    db = inject('db')
    lst = db((db.TblItemTopics.topic_id==topic_id)&(db.TblItemTopics.item_type=='E')).select()
    dic = dict()
    for rec in lst:
        if rec.item_id not in dic:
            dic[rec.item_id] = []
        dic[rec.item_id] = dic[rec.item_id] + [rec.id]
    ndel = 0
    for item_id in dic:
        lst1 = dic[item_id][1:]
        for id in lst1:
            ndel += 1
            db(db.TblItemTopics.id==id).delete()
    return ndel

def make_all_item_topics_unique():
    db = inject('db')
    topics = db(db.TblTopics).select()
    dups = []
    for topic in topics:
        ndel = make_item_topics_unique(topic.id)
        if ndel > 0:
            s = '{} {} had {} dups'.format(topic.id, topic.name, ndel)
            dups.append(s)