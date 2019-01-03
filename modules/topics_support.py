from injections import inject

def recalc_keywords_str(item_type, item_id):
    db = inject('db')
    tables = dict(
        M=db.TblMembers,
        E=db.TblEvents,
        P=db.TblPhotos,
        T=db.TblTerms,
        V=db.TblVideos
    )
    tbl = tables[item_type]
    q = (db.TblItemTopics.item_id==item_id) & (db.TblItemTopics.item_type==item_type) & (db.TblTopics.id==db.TblItemTopics.topic_id)
    lst = db(q).select()
    topic_names = [r.TblTopics.name for r in lst]
    topics_str = ';'.join(topic_names)
    if item_type in 'TV':
        db(tbl.id==item_id).update(keywords=topics_str)
    else:
        db(tbl.id==item_id).update(KeyWords=topics_str)

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
    cmd = """
        SELECT TblTopicGroups.parent, array_agg(TblTopicGroups.child)
        FROM TblTopicGroups
        GROUP BY TblTopicGroups.parent;
    """

    lst = db.executesql(cmd)
    return lst

def fix_topic_groups(): #one time for upgrade
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
