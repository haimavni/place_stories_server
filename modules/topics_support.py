from .injections import inject

def recalc_keywords_str(story_id):
    db = inject('db')
    q = (db.TblItemTopics.story_id==story_id) & (db.TblTopics.id==db.TblItemTopics.topic_id)
    lst = db(q).select()
    topic_names = [r.TblTopics.name for r in lst]
    topics_str = '; '.join(topic_names)
    db(db.TblStories.id==story_id).update(keywords=topics_str)

def recalc_all_keywords():
    db = inject('db')
    for srec in db(db.TblStories.deleted!=True).select(db.TblStories.id):
        recalc_keywords_str(srec.id)

def item_list_to_grouped_options(item_list):
    groups = dict()
    for item in item_list:
        if item.group_number not in groups:
            groups[item.group_number] = []
        groups[item.group_number].append(item.option)
    result = []
    for g in sorted(groups):
        result.append(groups[g])
    return result

def get_topic_groups():
    db = inject('db')
    if db(db.TblTopicGroups).isempty():
        return []
    cmd = """
        SELECT "TblTopicGroups"."parent", array_agg("TblTopicGroups"."child")
        FROM "TblTopicGroups"
        GROUP BY "TblTopicGroups"."parent";
    """

    lst = db.executesql(cmd)
    return lst

def calculate_all_story_keywords(): #not in use. one time for upgrade
    db = inject('db')
    q = (db.TblItemTopics.story_id == db.TblStories.id) 
    q &= (db.TblTopics.id == db.TblItemTopics.topic_id)
    q &= (db.TblTopics.topic_kind == 2)
    #lst = db(q)._select() #helped to create the sql command...
    cmd = '''
        SELECT "TblItemTopics"."story_id", array_agg("TblTopics"."name") FROM "TblTopics", "TblItemTopics", "TblStories" 
        WHERE (("TblItemTopics"."story_id" = "TblStories"."id") AND ("TblTopics"."id" = "TblItemTopics"."topic_id"))
        GROUP BY "TblItemTopics"."story_id";
    '''
    lst = db.executesql(cmd)
    for r in lst:
        keywords = '; '.join(r[1])
        db(db.TblStories.id==r[0]).update(keywords=keywords)
    n = len(lst)

def fix_topic_groups(): #not in use. one time for upgrade
    db = inject('db')
    for r in db(db.TblTopics.usage != '').select():
        usage = ''.join(sorted(list(set(list(r.usage)))))
        r.update_record(usage=usage, topic_kind=2)
    lst = get_topic_groups()
    for item in lst:
        g, gm = item
        topics = db(db.TblTopics.id.belongs(gm)).select(db.TblTopics.usage)
        uc = [r.usage for r in topics]
        usage = combined_usage(uc)
        db(db.TblTopics.id==g).update(usage=usage, topic_kind=1)
        
def combined_usage(uc):
    usage = ''
    for u in uc:
        for c in u:
            if c not in usage:
                usage += c
    usage = sorted(usage)
    usage = ''.join(usage)
    return usage

def add_a_topic(topic_name):
    db, User_Error = inject('db', 'User_Error')
    if db(db.TblTopics.name==topic_name).count() > 0:
        raise User_Error('!stories.topic-already-exists')
    new_topic_id = db.TblTopics.insert(name=topic_name, usage='', topic_kind=0)
    return new_topic_id

def topic_name(topic_id):
    db = inject('db')
    return db(db.TblTopics.id==topic_id).select().first().name

def rename_a_topic(topic_id, new_name):
    db = inject('db')
    rec = db(db.TblTopics.id==topic_id).select().first()
    old_name = rec.name
    if new_name == rec.name:
        return
    rec.update_record(name = new_name)
    #todo: recalculate keyword list for all relevant stories
    
def fix_is_tagged(first=0, chunk=100000):
    db, comment = inject('db', 'comment')
    comment("entered fix is tagged")
    cnt = 0
    for story in db((db.TblStories.is_tagged==None) & (db.TblStories.deleted!=True)).select():
        cnt += 1
        story.update_record(is_tagged = False)
    db.commit()
    cnt1 = 0
    for rec in db(db.TblItemTopics).select(limitby=(first,first+chunk)):
        cnt1 += 1
        story = db(db.TblStories.id==rec.story_id).select().first()
        if story:
            story.update_record(is_tagged=True)
    db.commit()
    comment("finished fix is tagged")
    
