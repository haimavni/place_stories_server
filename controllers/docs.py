import datetime
from docs_support import save_uploaded_doc, doc_url
from members_support import calc_grouped_selected_options, calc_all_tags, get_tag_ids
from date_utils import date_of_date_str, parse_date, get_all_dates, update_record_dates, fix_record_dates_in, fix_record_dates_out
import stories_manager

@serve_json
def upload_doc(vars):
    user_id = vars.user_id or auth.current_user()
    comment("start handling uploaded doc file")
    user_id = int(vars.user_id) if vars.user_id else auth.current_user()
    fil = vars.file
    result = save_uploaded_doc(fil.name, fil.BINvalue, user_id)
    return dict(upload_result=result)

@serve_json
def get_doc_list(vars):
    params = vars.params
    if params.checked_doc_list:
        lst0 = db(db.TblDocs.story_id.belongs(params.checked_doc_list)).select()
        lst0 = [rec for rec in lst0]
        for rec in lst0:
            rec.checked = True
    else:
        lst0 = []
    selected_topics = params.selected_topics or []
    if selected_topics:
        lst = get_doc_list_with_topics(params)
    else:
        q = make_docs_query(params)
        lst = db(q).select(orderby=~db.TblDocs.id)
    selected_doc_list = params.selected_doc_list
    lst = [rec for rec in lst if rec.story_id not in params.checked_doc_list]
    lst = lst0 + lst
    doc_list = [rec for rec in lst]
    for rec in doc_list:
        fix_record_dates_out(rec)
        story = get_story_by_id(rec.story_id)
        rec.story = story
        rec.doc_url = doc_url(rec.story_id)
    return dict(doc_list=doc_list, no_results=not doc_list)

@serve_json
def delete_checked_docs(vars):
    checked_doc_list = vars.params.checked_doc_list
    db(db.TblDocs.story_id.belongs(checked_doc_list)).update(deleted=True)
    db(db.TblStories.id.belongs(checked_doc_list)).update(deleted=True)
    return dict()

@serve_json
def apply_to_selected_docs(vars):
    all_tags = calc_all_tags()
    params = vars.params
    sdl = params.checked_doc_list
    if params.docs_date_str:
        dates_info = dict(
            doc_date = (params.docs_date_str, params.docs_date_span_size)
        )
    else:
        dates_info = None

    st = params.selected_topics
    added = []
    deleted = []
    changes = dict()
    for story_id in sdl:
        curr_tag_ids = set(get_tag_ids(story_id, 'D'))
        for tpc in st:
            topic = tpc.option
            ###item = dict(item_id=doc_id, topic_id=topic.id)
            drec = db(db.TblDocs.story_id==story_id).select().first()
            doc_id = drec.id
            if topic.sign=="plus" and topic.id not in curr_tag_ids:
                new_id = db.TblItemTopics.insert(item_type='D', item_id=doc_id, topic_id=topic.id, story_id=story_id) 
                curr_tag_ids |= set([topic.id])
                ###added.append(item)
                topic_rec = db(db.TblTopics.id==topic.id).select().first()
                if 'D' not in topic_rec.usage:
                    usage = topic_rec.usage + 'D'
                    topic_rec.update_record(usage=usage, topic_kind=2) #topic is simple 
            elif topic.sign=="minus" and topic.id in curr_tag_ids:
                q = (db.TblItemTopics.item_type=='D') & (db.TblItemTopics.item_id==doc_id) & (db.TblItemTopics.topic_id==topic.id)
                curr_tag_ids -= set([topic.id])
                ###deleted.append(item)
                db(q).delete()
        curr_tags = [all_tags[tag_id] for tag_id in curr_tag_ids]
        keywords = "; ".join(curr_tags)
        changes[doc_id] = dict(keywords=keywords, doc_id=doc_id)
        rec = db(db.TblDocs.id==doc_id).select().first()
        rec.update_record(keywords=keywords)  #todo: remove this line soon
        rec = db(db.TblStories.id==rec.story_id).select().first()
        rec.update_record(keywords=keywords)
        if dates_info:
            update_record_dates(rec, dates_info)
    ###changes = [changes[doc_id] for doc_id in sdl]
    ###ws_messaging.send_message('DOC-TAGS-CHANGED', group='ALL', changes=changes)
    return dict()

#----------------support functions-----------------

def get_doc_list_with_topics(vars):
    first = True
    topic_groups = calc_grouped_selected_options(vars.selected_topics)
    for topic_group in topic_groups:
        q = make_docs_query(vars) #if we do not regenerate it the query becomes accumulated and necessarily fails
        q &= (db.TblItemTopics.item_id==db.TblDocs.id) & (db.TblItemTopics.item_type.like('%D%'))
        ##topic_ids = [t.id for t in topic_group]
        sign = topic_group[0]
        topic_group = topic_group[1:]
        q1 = db.TblItemTopics.topic_id.belongs(topic_group)
        if sign == 'minus':
            q1 = ~q1
        q &= q1
        lst = db(q).select(orderby=~db.TblDocs.id)
        lst = [rec.TblDocs for rec in lst]
        bag1 = set(r.id for r in lst)
        if first:
            first = False
            bag = bag1
        else:
            bag &= bag1
    dic = {}
    for r in lst:
        dic[r.id] = r
    result = [dic[id] for id in bag]
    return result

def make_docs_query(params):
    q = (db.TblDocs.deleted!=True)
    if params.selected_days_since_upload:
        days = params.selected_days_since_upload.value
        if days:
            upload_date = datetime.datetime.today() - datetime.timedelta(days=days)
            q &= (db.TblDocs.upload_date >= upload_date)
    opt = params.selected_uploader
    if opt == 'mine':
        q &= (db.TblDocs.uploader==params.user_id)
    elif opt == 'users':
        q &= (db.TblDocs.uploader!=None)
    opt = params.selected_dates_option
    if opt == 'selected_dates_option':
        pass
    elif opt == 'dated':
        q &= (db.TblDocs.doc_date != NO_DATE)
    elif opt == 'undated':
        q &= (db.TblDocs.doc_date == NO_DATE)
    if params.selected_docs:
        q &= (db.TblDocs.story_id.belongs(params.selected_docs))
    return q

def get_story_by_id(story_id):
    sm = stories_manager.Stories()
    return sm.get_story(story_id)


