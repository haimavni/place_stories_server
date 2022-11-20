import datetime
from docs_support import save_uploaded_doc, doc_url, calc_doc_story, create_uploading_doc, save_uploading_chunk, \
    handle_loaded_doc
from members_support import calc_grouped_selected_options, calc_all_tags, get_tag_ids, init_query, get_topics_query, get_object_topics, photos_folder
from date_utils import date_of_date_str, parse_date, get_all_dates, update_record_dates, fix_record_dates_in, \
    fix_record_dates_out
import stories_manager
from gluon.storage import Storage


@serve_json
def upload_doc(vars):
    user_id = vars.user_id or auth.current_user()
    comment("start handling uploaded doc file")
    user_id = int(vars.user_id) if vars.user_id else auth.current_user()
    fil = vars.file
    result = save_uploaded_doc(fil.name, fil.BINvalue, user_id)
    if result != 'duplicate':
        calc_doc_story(result)
    return dict(upload_result=result)


@serve_json
def upload_chunk(vars):
    if vars.what == 'start':
        result = create_uploading_doc(vars.file_name, vars.crc, vars.user_id)
        if result.duplicate:
            return dict(duplicate=result.duplicate)
        return dict(record_id=result.record_id)
    elif vars.what == 'save':
        comment(f"upload chunk. vars.record_id: {vars.record_id}, vars.start: {vars.start}")
        fil = vars.file
        blob = bytearray(fil.BINvalue)
        save_uploading_chunk(vars.record_id, vars.start, blob)
        if vars.is_last:
            handle_loaded_doc(vars.record_id)
        return dict()

    return dict()


@serve_json
def get_doc_list(vars):
    params = vars.params
    if params.checked_doc_list:
        q = (db.TblDocs.story_id.belongs(params.checked_doc_list)) & (db.TblStories.id == db.TblDocs.story_id)
        lst0 = db(q).select()
        lst0 = [rec for rec in lst0]
        for rec in lst0:
            rec.TblDocs.checked = True
    else:
        lst0 = []
    selected_topics = params.selected_topics or []
    q = make_docs_query(params)
    lst = db(q).select(orderby=~db.TblDocs.id)
    lst = [rec for rec in lst if rec.TblDocs.story_id not in params.checked_doc_list]
    lst = lst0 + lst
    doc_list = []
    for rec1 in lst:
        rec = rec1.TblDocs
        fix_record_dates_out(rec)
        story = get_story_by_id(rec.story_id)
        rec.story = story
        rec.doc_url = doc_url(rec.story_id)
        rec.doc_jpg_url = rec.doc_url.replace('/docs/', '/docs/pdf_jpgs/').replace('.pdf', '.jpg')
        rec.keywords = rec1.TblStories.keywords
        doc_list.append(rec)
    return dict(doc_list=doc_list, no_results=not doc_list)


@serve_json
def delete_checked_docs(vars):
    checked_doc_list = vars.params.checked_doc_list
    db(db.TblDocs.story_id.belongs(checked_doc_list)).update(deleted=True)
    db(db.TblStories.id.belongs(checked_doc_list)).update(deleted=True)
    return dict()


@serve_json
def apply_topics_to_doc(vars):
    all_tags = calc_all_tags()
    doc_id = int(vars.doc_id)
    rec = db(db.TblDocs.id == doc_id).select().first()
    story_id = rec.story_id if rec else None
    topics = vars.topics
    curr_tag_ids = set(get_tag_ids(story_id, "D"))
    new_tag_ids = set([t.id for t in topics])
    added = set([])
    deleted = set([])
    for tag_id in new_tag_ids:
        if tag_id not in curr_tag_ids:
            added |= set([tag_id])
            db.TblItemTopics.insert(
                item_type="D",
                topic_id=tag_id,
                story_id=story_id)
            topic_rec = db(db.TblTopics.id == tag_id).select().first()
            if 'D' not in topic_rec.usage:
                usage = topic_rec.usage + 'D'
                topic_rec.update_record(usage=usage, topic_kind=2)  # simple topic

    for tag_id in curr_tag_ids:
        if tag_id not in new_tag_ids:
            deleted |= set([tag_id])
            q = (db.TblItemTopics.item_type == "D") & \
                (db.TblItemTopics.story_id == story_id) & \
                (db.TblItemTopics.topic_id == tag_id)
            # should remove 'P' from usage if it was the last one...
            db(q).delete()

    curr_tag_ids |= added
    curr_tag_ids -= deleted
    curr_tags = [all_tags[tag_id] for tag_id in curr_tag_ids]
    curr_tags = sorted(curr_tags)
    keywords = "; ".join(curr_tags)
    is_tagged = len(curr_tags) > 0
    srec = db(db.TblStories.id == rec.story_id).select().first()
    srec.update_record(keywords=keywords, is_tagged=is_tagged)
    # rec.update_record(Recognized=True)
    # rec.update_record(handled=True)

@serve_json
def apply_to_checked_docs(vars):
    all_tags = calc_all_tags()
    params = vars.params
    sdl = params.checked_doc_list
    if params.docs_date_str:
        dates_info = dict(
            doc_date=(params.docs_date_str, params.docs_date_span_size)
        )
    else:
        dates_info = None

    st = params.selected_topics
    added = []
    deleted = []
    changes = dict()
    new_topic_was_added = False
    for story_id in sdl:
        drec = db(db.TblDocs.story_id == story_id).select().first()  # get rid of _term_id_
        curr_tag_ids = set(get_tag_ids(story_id, 'D'))
        for tpc in st:
            topic = tpc.option
            doc_id = drec.id  # get rid of _term_id_
            if topic.sign == "plus" and topic.id not in curr_tag_ids:
                new_id = db.TblItemTopics.insert(item_type='D', topic_id=topic.id, story_id=story_id)
                curr_tag_ids |= set([topic.id])
                ###added.append(item)
                topic_rec = db(db.TblTopics.id == topic.id).select().first()
                if topic_rec.topic_kind == 0:  # never used
                    new_topic_was_added = True
                if 'D' not in topic_rec.usage:
                    usage = topic_rec.usage + 'D'
                    topic_rec.update_record(usage=usage, topic_kind=2)  # topic is simple
            elif topic.sign == "minus" and topic.id in curr_tag_ids:
                q = (db.TblItemTopics.item_type == 'D') & (db.TblItemTopics.story_id == story_id) & (
                            db.TblItemTopics.topic_id == topic.id)  # got rid of _item_id_
                curr_tag_ids -= set([topic.id])
                ###deleted.append(item)
                db(q).delete()
        curr_tags = [all_tags[tag_id] for tag_id in curr_tag_ids]
        keywords = "; ".join(curr_tags)
        changes[doc_id] = dict(keywords=keywords, doc_id=doc_id)
        rec = db(db.TblDocs.id == doc_id).select().first()
        rec = db(db.TblStories.id == rec.story_id).select().first()
        rec.update_record(keywords=keywords, is_tagged=bool(keywords))
        if dates_info:
            update_record_dates(rec, dates_info)
    ###changes = [changes[doc_id] for doc_id in sdl]
    ###ws_messaging.send_message('DOC-TAGS-CHANGED', group='ALL', changes=changes)
    return dict(new_topic_was_added=new_topic_was_added)


@serve_json
def get_doc_info(vars):
    doc_id = int(vars.doc_id)
    if vars.caller == 'docs':
        doc_rec = db(db.TblDocs.id == doc_id).select().first()
    else:
        doc_rec = db(db.TblDocs.story_about_id == doc_id).select().first()
        if not doc_rec:
            doc_rec = db(db.TblDocs.story_id == doc_id).select().first()
        if not doc_rec:
            comment(f'BUG!!! caller: {vars.caller}, doc_id: {doc_id}')
        doc_id = doc_rec.id
    all_dates = get_all_dates(doc_rec)
    doc_src = doc_url(doc_rec.story_id)
    doc_name = db(db.TblStories.id==doc_rec.story_id).select(db.TblStories.name).first().name
    doc_topics = get_object_topics(doc_rec.story_id, 'D')
    sm = stories_manager.Stories()
    story_about= sm.get_story(doc_rec.story_about_id)
    doc_story = sm.get_story(doc_rec.story_id)
    story_id = doc_story.story_id
    chatroom_id = doc_story.chatroom_id
    if not story_about:
        story_info = Storage(story_text=doc_story.preview, name=doc_name, used_for=STORY4DOCAB, preview=doc_story.preview)
        story_about = sm.add_story(story_info)
        doc_rec.update_record(story_about_id=story_about.story_id)
    member_ids = db(db.TblMembersDocs.doc_id==doc_id).select()
    member_ids = [m.member_id for m in member_ids]
    members = db(db.TblMembers.id.belongs(member_ids)).select()
    members = [Storage(id=member.id,
                       facePhotoURL=photos_folder('profile_photos') + (member.facePhotoURL or "dummy_face.png"),
                       full_name=member.first_name + ' ' + member.last_name)
               for member in members]

    return dict(doc=doc_rec,
                doc_id=doc_id,
                doc_src=doc_src,
                doc_name=doc_name,
                story_about=story_about,
                doc_topics=doc_topics,
                doc_date_str=all_dates.doc_date.date,
                doc_date_datespan=all_dates.doc_date.span,
                doc_date_dateunit=all_dates.doc_date.unit,
                story_id=story_id,
                chatroom_id=chatroom_id,
                members=members
                )


@serve_json
def update_doc_date(vars):
    # doc_date_str = vars.doc_date_str
    doc_dates_info = dict(
        doc_date=(vars.doc_date_str, int(vars.doc_date_datespan))
    )
    rec = db((db.TblDocs.id == int(vars.doc_id)) & (db.TblDocs.deleted != True)).select().first()
    update_record_dates(rec, doc_dates_info)
    return dict()

@serve_json
def update_doc_members(vars):
    doc_id = int(vars.doc_id)
    old_members = db(db.TblMembersDocs.doc_id==doc_id).select()
    old_members = [m.member_id for m in old_members]
    old_members_set = set(old_members)
    new_members = vars.member_ids
    new_members_set = set(new_members)
    deleted_members = [mid for mid in old_members if mid not in new_members_set]
    q = (db.TblMembersDocs.doc_id==doc_id) & (db.TblMembersDocs.member_id.belongs(deleted_members))
    db(q).delete()
    for mid in new_members:
        if mid not in old_members_set:
            db.TblMembersDocs.insert(doc_id=doc_id, member_id=mid)
    members = db(db.TblMembers.id.belongs(new_members)).select(db.TblMembers.id, db.TblMembers.facePhotoURL)
    for member in members:
        member.facePhotoURL = photos_folder('profile_photos') + (member.facePhotoURL or "dummy_face.png")
    return dict(members=members)

@serve_json
def update_story_preview(vars):
    comment(f"update story preview vars: {vars}")
    story_id = int(vars.story_id)
    story_about_id = int(vars.story_about_id)
    story_rec = db(db.TblStories.id==story_id).select().first()
    story_about_rec = db(db.TblStories.id==story_about_id).select().first()
    story_about_rec.update_record(preview=story_rec.preview)
    return dict()

# ----------------support functions-----------------

def make_docs_query(params):
    q = init_query(db.TblDocs, params.editing)
    if params.days_since_upload:
        days = params.days_since_upload.value
        if days:
            upload_date = datetime.datetime.today() - datetime.timedelta(days=days)
            q &= (db.TblDocs.upload_date >= upload_date)
    opt = params.selected_uploader
    if opt == 'mine':
        q &= (db.TblDocs.uploader == params.user_id)
    elif opt == 'users':
        q &= (db.TblDocs.uploader != None)
    opt = params.selected_dates_option
    if opt == 'selected_dates_option':
        pass
    elif opt == 'dated':
        q &= (db.TblDocs.doc_date != NO_DATE)
    elif opt == 'undated':
        q &= (db.TblDocs.doc_date == NO_DATE)
    if params.selected_docs:
        q &= (db.TblDocs.story_id.belongs(params.selected_docs))
    if params.selected_topics:
        q1 = get_topics_query(params.selected_topics)
        q &= q1
    return q


def get_story_by_id(story_id):
    sm = stories_manager.Stories()
    return sm.get_story(story_id)
