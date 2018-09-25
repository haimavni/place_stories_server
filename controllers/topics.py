import ws_messaging

@serve_json
def get_topic_list(vars):
    topic_groups = get_topic_groups()
    if vars.usage:
        usage = vars.usage
    elif vars.params:
        usage = ""
        topic_chars = 'xMEPTxxxV'
        story_types = vars.params.selected_story_types
        story_types = [st.id for st in story_types]
        for t in story_types:
            usage += topic_chars[t] 
    else:
        usage = ""
    q = db.TblTopics.id > 0
    if usage:
        q1 = None
        for c in usage:
            if q1:
                q1 |= (db.TblTopics.usage.like("%" + c + "%"))
            else:
                q1 = (db.TblTopics.usage.like("%" + c + "%"))
        q &= q1
    topic_list = db(q).select(orderby=~db.TblTopics.is_group | db.TblTopics.name)
    topic_list = [dict(name=rec.name, id=rec.id, is_group=rec.is_group) for rec in topic_list if rec.name]
    q = db.TblPhotographers.id > 0
    if usage in ('P', 'V'):
        q &= db.TblPhotographers.kind.like('%' + usage + '%')
    photographer_list = db(q).select(orderby=db.TblPhotographers.name)
    photographer_list = [dict(name=rec.name, id=rec.id) for rec in photographer_list if rec.name]
    return dict(topic_list=topic_list, topic_groups=topic_groups, photographer_list=photographer_list)

@serve_json 
def remove_topic(vars):
    topic_id = vars.topic_id
    lst = db(db.TblItemTopics.topic_id==topic_id).select()
    lst = [Storage(item_type=rec.item_type, item_id=rec.item_id) for rec in lst]
    n = db(db.TblTopics.id==topic_id).delete()
    for rec in lst:
        recalc_keywords_str(rec.item_type, rec.item_id)
    return dict()
   
def recalc_keywords_str(item_type, item_id):
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

@serve_json
def save_tag_merges(vars):
    gst = vars.selected_topics
    if gst:
        gst = item_list_to_grouped_options(gst)
        for topic_group in gst:
            topic0 = topic_group[0]
            rec0 = db(db.TblTopics.id==topic0.id).select().first()
            for topic in topic_group[1:]:
                rec = db(db.TblTopics.id==topic.id).select().first()
                if not rec.usage:
                    continue
                for c in rec.usage:
                    if c not in rec0.usage:
                        rec0.usage += c
                        rec0.update_record(usage=rec0.usage)
    
                db(db.TblItemTopics.topic_id==rec.id).update(topic_id=rec0.id)
                db(db.TblTopics.id==rec.id).delete()

    gsp = vars.selected_photographers
    if gsp:
        gsp = item_list_to_grouped_options(gsp)
        for p_group in gsp:
            p0 = p_group[0]
            rec0 = db(db.TblPhotographers.id==p0.id).select().first()
            for p in p_group[1:]:
                rec = db(db.TblPhotographers.id==p.id).select().first()
                db(db.TblPhotos.photographer_id==rec.id).update(photographer_id=rec0.id)
            db(db.TblPhotographers.id==rec.id).delete()

    ws_messaging.send_message(key='TAGS_MERGED', group='ALL')
    return dict()

@serve_json
def add_photographer(vars):
    photographer_name = vars.photographer_name
    if not db(db.TblPhotographers.name==photographer_name).isempty():
        raise User_Error("!photos.photographer-already-exists")
    db.TblPhotographers.insert(name=photographer_name)
    ws_messaging.send_message(key='PHOTOGRAPHER_ADDED', group='ALL', photographer_name=photographer_name)
    return dict()

@serve_json
def remove_photographer(vars):
    photographer = vars.photographer_name;
    raise Exception('Photographer removal not ready yet')

@serve_json
def rename_photographer(vars):
    db(db.TblPhotographers.id==int(vars.id)).update(name=vars.name)
    return dict()

@serve_json
def rename_topic(vars):
    db(db.TblTopics.id==int(vars.id)).update(name=vars.name)
    #todo: update all keywords in the system...
    return dict()

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

@serve_json
def add_topic(vars):
    if db(db.TblTopics.name==vars.topic_name).count() > 0:
        raise User_Error('!stories.topic-already-exists')
    idx = db.TblTopics.insert(name=vars.topic_name, usage='')
    return dict(new_topic_id=idx)

@serve_json
def add_topic_group(vars):
    gst = vars.selected_topics
    if not gst:
        return dict()
    gst = item_list_to_grouped_options(gst)
    if len(gst) != 2 or len(gst[0]) != 1:
        raise User_Error('!stories.invalid-group-data')
    #todo: ensure no cyclic
    topic_ids = set([topic.id for topic in gst[1]])
    group_id = gst[0][0].id
    old_topic_ids = db(db.TblTopicGroups.parent==group_id).select()
    old_topic_ids = set([topic.child for topic in old_topic_ids])
    deleted_topic_ids = old_topic_ids - topic_ids
    new_topic_ids = topic_ids - old_topic_ids
    for tid in new_topic_ids:
        db.TblTopicGroups.insert(parent=group_id, child=tid)
    for tid in deleted_topic_ids:
        db((db.TblTopicGroups.parent==group_id) & (db.TblTopicGroups.child==tid)).delete()
    db(db.TblTopics.id==group_id).update(is_group=True)
    return dict()

def get_topic_groups():
    cmd = """
        SELECT TblTopicGroups.parent, array_agg(TblTopicGroups.child)
        FROM TblTopicGroups
        GROUP BY TblTopicGroups.parent;
    """

    lst = db.executesql(cmd)
    return lst
    
