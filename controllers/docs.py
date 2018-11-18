import datetime
from docs_support import save_uploaded_doc
from date_utils import date_of_date_str, parse_date, get_all_dates, update_record_dates, fix_record_dates_in, fix_record_dates_out

@serve_json
def upload_doc(vars):
    user_id = vars.user_id or auth.current_user()
    comment("start handling uploaded doc files")
    user_id = int(vars.user_id) if vars.user_id else auth.current_user()
    fil = vars.file
    result = save_uploaded_doc(fil.name, fil.BINvalue, user_id)
    return dict(upload_result=result)

@serve_json
def get_doc_list(vars):
    selected_topics = vars.selected_topics or []
    if selected_topics:
        lst = get_doc_list_with_topics(vars)
    else:
        q = make_docs_query(vars)
        lst = db(q).select()
    selected_doc_list = vars.selected_doc_list
    result = []
    if selected_doc_list:
        lst1 = db(db.Tbldocs.id.belongs(selected_doc_list)).select()
        lst1 = [rec for rec in lst1]
        for rec in lst1:
            rec.selected = True
    else:
        lst1 = []
    lst1_ids = [rec.id for rec in lst1]
    lst = [rec for rec in lst if rec.id not in lst1_ids]
    lst = lst1 + lst
    ##lst = db(db.Tbldocs.deleted != True).select()
    doc_list = [rec for rec in lst]
    for rec in doc_list:
        fix_record_dates_out(rec)
    return dict(doc_list=doc_list)

@serve_json
def delete_selected_docs(vars):
    selected_doc_list = vars.selected_doc_list
    db(db.TblPhotos.id.belongs(selected_doc_list)).update(deleted=True)
    return dict()

@serve_json
def apply_to_selected_docs(vars):
    all_tags = calc_all_tags()
    sdl = vars.selected_doc_list
    if vars.docs_date_str:
        dates_info = dict(
            doc_date = (vars.docs_date_str, vars.docs_date_span_size)
        )
    else:
        dates_info = None

    st = vars.selected_topics
    added = []
    deleted = []
    changes = dict()
    for doc_id in sdl:
        curr_tag_ids = set(get_tag_ids(doc_id, 'D'))
        for tpc in st:
            topic = tpc.option
            item = dict(item_id=doc_id, topic_id=topic.id)
            if topic.sign=="plus" and topic.id not in curr_tag_ids:
                drec = db(db.TblDocs.id==doc_id).select().first()
                story_id = drec.story_id if drec else None
                if not story_id:
                    continue
                new_id = db.TblItemTopics.insert(item_type='D', item_id=doc_id, topic_id=topic.id, story_id=story_id) 
                curr_tag_ids |= set([topic.id])
                added.append(item)
                topic_rec = db(db.TblTopics.id==topic.id).select().first()
                if 'D' not in topic_rec.usage:
                    usage = topic_rec.usage + 'D'
                    topic_rec.update_record(usage=usage)
            elif topic.sign=="minus" and topic.id in curr_tag_ids:
                q = (db.TblItemTopics.item_type=='D') & (db.TblItemTopics.item_id==doc_id) & (db.TblItemTopics.topic_id==topic.id)
                curr_tag_ids -= set([topic.id])
                deleted.append(item)
                db(q).delete()
        curr_tags = [all_tags[tag_id] for tag_id in curr_tag_ids]
        keywords = "; ".join(curr_tags)
        changes[doc_id] = dict(keywords=keywords, doc_id=doc_id)
        rec = db(db.TblDocs.id==doc_id).select().first()
        rec.update_record(keywords=keywords)
        if dates_info:
            update_record_dates(rec, dates_info)
    changes = [changes[doc_id] for doc_id in sdl]
    ws_messaging.send_message('DOC-TAGS-CHANGED', group='ALL', changes=changes)
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
        lst = db(q).select()
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

def make_docs_query(vars):
    q = (db.TblDocs.deleted!=True)
    if vars.selected_days_since_upload:
        days = vars.selected_days_since_upload.value
        if days:
            upload_date = datetime.datetime.today() - datetime.timedelta(days=days)
            q &= (db.TblDocs.upload_date >= upload_date)
    opt = vars.selected_uploader
    if opt == 'mine':
        q &= (db.TblDocs.uploader==vars.user_id)
    elif opt == 'users':
        q &= (db.TblDocs.uploader!=None)
    opt = vars.selected_dates_option
    if opt == 'selected_dates_option':
        pass
    elif opt == 'dated':
        q &= (db.TblDocs.doc_date != NO_DATE)
    elif opt == 'undated':
        q &= (db.TblDocs.doc_date == NO_DATE)
    return q



