import ws_messaging
from topics_support import *
from folders import url_folder

@serve_json
def get_topic_list(vars):
    topic_groups = get_topic_groups()
    if vars.usage:
        usage = vars.usage
    elif vars.params and vars.params.selected_story_types:
        usage = ""
        topic_chars = 'xMEPTxxxVDUxAxS'  #see db_gbs.py STORY4... to interpret the mapping. Note - "U" is for audio
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
        ### q1 |= (db.TblTopics.usage=='') #for upper-level topics # groups must also have usage!
        q &= q1
        
    topic_list = db(q).select(orderby=db.TblTopics.topic_kind | db.TblTopics.name)
    topic_list = [dict(name=rec.name, description=rec.description, id=rec.id, topic_kind=rec.topic_kind, usage=rec.usage) for rec in topic_list if rec.name]
    q = db.TblPhotographers.id > 0
    if usage in ('P', 'V'):
        q &= db.TblPhotographers.kind.like('%' + usage + '%')
    photographer_list = db(q).select(orderby=db.TblPhotographers.name)
    photographer_list = [dict(name=rec.name, id=rec.id, topic_kind=2) for rec in photographer_list if rec.name]
    return dict(topic_list=topic_list, topic_groups=topic_groups, photographer_list=photographer_list)

@serve_json
def print_topics_file(vars):
    q = db.TblTopics.topic_kind > 0
    topic_list = db(q).select(orderby=db.TblTopics.topic_kind | db.TblTopics.name)
    out_name = log_path() + "topics.txt"
    with open(out_name, "w", encoding="utf-8") as out_file:
        print_topics(topic_list, out_file)
    topics_file_url = url_folder("logs") + "topics.txt"
    return dict(topics_file_url=topics_file_url, topic_list=topic_list)

def print_topics(topic_list, out_file, level=0):
    for topic_rec in topic_list:
        out_file.write(' ' * level * 4)
        out_file.write(topic_rec.name + "\n")
        if topic_rec.topic_kind==1: #compound
            topic_children = db(db.TblTopicGroups.parent==topic_rec.id).select()
            topic_children = [tc.child for tc in topic_children]
            lst = db(db.TblTopics.id.belongs(topic_children)).select(orderby=db.TblTopics.topic_kind | db.TblTopics.name)
            print_topics(lst, out_file, level+1)

@serve_json 
def remove_topic(vars):
    topic_id = vars.topic_id
    lst = db(db.TblItemTopics.topic_id==topic_id).select()
    lst = [Storage(item_type=rec.item_type, story_id=rec.story_id) for rec in lst]
    db(db.TblTopics.id==topic_id).delete()
    for rec in lst:
        recalc_keywords_str(rec.story_id)
    return dict()
   
@serve_json
def save_tag_merges(vars):
    gst = vars.selected_topics
    if gst:
        gst = item_list_to_grouped_options(gst)
        for topic_group in gst:
            topic0 = topic_group[0]
            rec0 = db(db.TblTopics.id==topic0.id).select().first()
            for topic in topic_group[1:]:
                rec = db(db.TblTopics.id == topic.id).select().first()
                if not rec.usage:
                    continue
                for char in rec.usage:
                    if char not in rec0.usage:
                        rec0.usage += char
                        rec0.update_record(usage=rec0.usage)
    
                db(db.TblItemTopics.topic_id == rec.id).update(topic_id=rec0.id)
                db(db.TblTopics.id == rec.id).delete()

    gsp = vars.selected_photographers
    if gsp:
        gsp = item_list_to_grouped_options(gsp)
        for p_group in gsp:
            p0 = p_group[0]
            rec0 = db(db.TblPhotographers.id == p0.id).select().first()
            for p in p_group[1:]:
                rec = db(db.TblPhotographers.id == p.id).select().first()
                db(db.TblPhotos.photographer_id == rec.id).update(photographer_id=rec0.id)
            db(db.TblPhotographers.id == rec.id).delete()

    ws_messaging.send_message(key='TAGS_MERGED', group='ALL')
    return dict()

@serve_json
def add_photographer(vars):
    photographer_name = vars.photographer_name
    if not db(db.TblPhotographers.name == photographer_name).isempty():
        raise User_Error("!photos.photographer-already-exists")
    db.TblPhotographers.insert(name=photographer_name)
    ws_messaging.send_message(key='PHOTOGRAPHER_ADDED', group='ALL', photographer_name=photographer_name)
    return dict()

@serve_json
def remove_photographer(vars):
    pid = vars.photographer.id
    np = db((db.TblPhotos.photographer_id==pid) & (db.TblPhotos.deleted != True)).count()
    nv = db((db.TblVideos.photographer_id==pid) & (db.TblVideos.deleted != True)).count()
    if np or nv:
        raise User_Error('!photos.photographer-has-photos')
    db(db.TblPhotographers.id==pid).delete()
    return dict()

@serve_json
def rename_photographer(vars):
    db(db.TblPhotographers.id == int(vars.id)).update(name=vars.name)
    return dict()

@serve_json
def rename_topic(vars):
    db(db.TblTopics.id == int(vars.id)).update(name=vars.name)
    #todo: update all keywords in the system...
    return dict()

@serve_json
def add_topic(vars):
    new_topic_id = add_a_topic(vars.topic_name)
    return dict(new_topic_id=new_topic_id)

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
    topic_usage = [topic.usage for topic in gst[1]]
    topic_usage = combined_usage(topic_usage)
    group_id = gst[0][0].id
    old_topic_ids = db(db.TblTopicGroups.parent==group_id).select()
    old_topic_ids = set([topic.child for topic in old_topic_ids])
    deleted_topic_ids = old_topic_ids - topic_ids
    new_topic_ids = topic_ids - old_topic_ids
    for tid in new_topic_ids:
        db.TblTopicGroups.insert(parent=group_id, child=tid)
    for tid in deleted_topic_ids:
        db((db.TblTopicGroups.parent==group_id) & (db.TblTopicGroups.child==tid)).delete()
    db(db.TblTopics.id==group_id).update(topic_kind=1, usage=topic_usage)
    return dict()

@serve_json
def update_topic_name_and_description(vars):
    topic = vars.topic
    n = db((db.TblTopics.id!=topic.id) & (db.TblTopics.name==topic.name)).count()
    if n > 0:
        return dict(user_error='multi-select.duplicate')
    db(db.TblTopics.id==topic.id).update(name=topic.name, description=topic.description)
    return dict()

@serve_json
def create_new_book(vars):
    if not db(db.TblBooks.name==vars.book_name).isempty():
        raise Exception("Name is already in use")
    book_id = db.TblBooks.insert(name=vars.book_name)
    return dict(book_id=book_id)

@serve_json
def modify_book_info(vars):
    #if vars.delete: delete the book
    book = vars.book
    book_id = int(book.id)
    book_rec = db(db.TblBooks.id==book_id).select().first()
    book_rec.update_record(name=book.name, description=book.description)
    return dict()

@serve_json
def remove_book(vars):
    book = vars.book
    db(db.TblStories.book_id==book.id).update(book_id=None)
    db(db.TblBooks.id==book.id).delete()
    return dict()

@serve_json
def remove_story_from_book(vars):
    book_id = vars.book_id
    story_id = vars.story_id
    story_rec = db(db.TblStories.id==story_id)
    if (not story_rec) or story_rec.book_id != book_id:
        raise Exception('Book / story mismatch!')
    story_rec.update(book_id=None)
    return dict()