import datetime
from docs_support import save_uploaded_doc, doc_url, doc_jpg_url, \
    doc_segment_url, doc_segment_jpg_url, create_uploading_doc, save_uploading_chunk, \
    handle_loaded_doc, save_doc_segment_thumbnail, save_uploaded_thumbnail
from members_support import calc_grouped_selected_options, calc_all_tags, get_tag_ids, init_query, get_topics_query, get_object_topics, photos_folder
from date_utils import date_of_date_str, parse_date, get_all_dates, update_record_dates, fix_record_dates_in, \
    fix_record_dates_out
import stories_manager
from gluon.storage import Storage
from folders import RESIZED, ORIG, SQUARES, PROFILE_PHOTOS

@serve_json
def upload_doc(vars):
    user_id = vars.user_id or auth.current_user()
    comment("start handling uploaded doc file")
    user_id = int(vars.user_id) if vars.user_id else auth.current_user()
    fil = vars.file
    result = save_uploaded_doc(fil.name, fil.BINvalue, user_id)
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
        # for the filters to work
        rec.name = story.name
        rec.source = story.source
        rec.doc_url = doc_url(None, rec)
        rec.doc_jpg_url = doc_jpg_url(None, rec)
        rec.keywords = rec1.TblStories.keywords
        rec.name = rec1.TblStories.name
        rec.doc_date = rec1.TblStories.story_date
        doc_list.append(rec)
    active_doc_segments = db(db.TblDocSegments).count() > 0
    return dict(doc_list=doc_list, no_results=not doc_list, active_doc_segments=active_doc_segments)


@serve_json
def get_doc_segment_list(vars):
    params = vars.params
    if params.checked_doc_list:
        q = (db.TblDocSegments.story_id.belongs(params.checked_doc_list)) & \
            (db.TblStories.id == db.TblDocSegments.story_id) \
            (db.TblDocs.id == db.TblDocSegments.doc_id)
        lst0 = db(q).select()
        lst0 = [rec for rec in lst0]
        for rec in lst0:
            rec.TblDocSegments.checked = True
    else:
        lst0 = []
    q = make_doc_segments_query(params)
    lst = db(q).select(orderby=~db.TblDocSegments.id)
    lst = [rec for rec in lst if rec.TblDocSegments.story_id not in params.checked_doc_list]
    lst = lst0 + lst
    doc_segment_list = []
    for rec1 in lst:
        rec = rec1.TblDocSegments
        rec.segment_id = rec.id
        story_rec = rec1.TblStories
        fix_record_dates_out(story_rec)
        story = rec1.TblStories
        rec.story = story
        #for the filters to work
        rec.name = story.name
        rec.source = story.source
        rec.doc_url = doc_segment_url(None, rec1)
        rec.doc_jpg_url = doc_segment_jpg_url(None, rec1)
        rec.keywords = rec1.TblStories.keywords
        # rec.name = rec1.TblStories.name
        rec.doc_date = rec1.TblStories.story_date
        doc_segment_list.append(rec)
    return dict(doc_segment_list=doc_segment_list, no_results=not doc_segment_list)


@serve_json
def delete_checked_docs(vars):
    checked_doc_list = vars.params.checked_doc_list
    db(db.TblDocs.story_id.belongs(checked_doc_list)).update(deleted=True)
    db(db.TblStories.id.belongs(checked_doc_list)).update(deleted=True)
    return dict()


@serve_json
def apply_topics_to_doc(vars):
    all_tags = calc_all_tags()
    if vars.doc_segment_id:
        doc_segment_id = int(vars.doc_segment_id)
        rec = db(db.TblDocSegments.id == doc_segment_id).select().first()
        topic_type = "S"
    else:
        doc_id = int(vars.doc_id)
        rec = db(db.TblDocs.id == doc_id).select().first()
        topic_type = "D"
    story_id = rec.story_id if rec else None
    topics = vars.topics
    curr_tag_ids = set(get_tag_ids(story_id, topic_type))
    new_tag_ids = set([t.id for t in topics])
    added = set([])
    deleted = set([])
    for tag_id in new_tag_ids:
        if tag_id not in curr_tag_ids:
            added |= set([tag_id])
            db.TblItemTopics.insert(
                item_type=topic_type,
                topic_id=tag_id,
                story_id=story_id)
            topic_rec = db(db.TblTopics.id == tag_id).select().first()
            if topic_type not in topic_rec.usage:
                usage = topic_rec.usage + topic_type
                topic_rec.update_record(
                    usage=usage, topic_kind=2)  # simple topic

    for tag_id in curr_tag_ids:
        if tag_id not in new_tag_ids:
            deleted |= set([tag_id])
            q = (db.TblItemTopics.item_type == topic_type) & \
                (db.TblItemTopics.story_id == story_id) & \
                (db.TblItemTopics.topic_id == tag_id)
            # should remove 'P' from usage if it was the last one...
            db(q).delete()

    curr_tag_ids |= added
    curr_tag_ids -= deleted
    curr_tags = [all_tags[tag_id] for tag_id in curr_tag_ids]
    curr_tags = sorted(curr_tags)
    keywords = KW_SEP.join(curr_tags)
    is_tagged = len(curr_tags) > 0
    srec = db(db.TblStories.id == rec.story_id).select().first()
    srec.update_record(keywords=keywords, is_tagged=is_tagged)
    return dict()
    # rec.update_record(recognized=True)
    # rec.update_record(handled=True)

@serve_json
def apply_to_checked_docs(vars):
    all_tags = calc_all_tags()
    params = vars.params
    topic_type = "S" if params.view_doc_segments else "D"
    sdl = params.checked_doc_list
    if params.docs_date_str:
        dates_info = dict(
            doc_date=(params.docs_date_str, params.docs_date_span_size)
        )
    else:
        dates_info = None

    st = params.selected_topics
    changes = dict()
    new_topic_was_added = False
    for story_id in sdl:
        # get rid of _term_id_
        drec = db(db.TblDocs.story_id == story_id).select().first()
        curr_tag_ids = set(get_tag_ids(story_id, topic_type))
        for tpc in st:
            topic = tpc.option
            doc_id = drec.id  # get rid of _term_id_
            if topic.sign == "plus" and topic.id not in curr_tag_ids:
                new_id = db.TblItemTopics.insert(item_type=topic_type, topic_id=topic.id, story_id=story_id)
                curr_tag_ids |= set([topic.id])
                # added.append(item)
                topic_rec = db(db.TblTopics.id == topic.id).select().first()
                if topic_rec.topic_kind == 0:  # never used
                    new_topic_was_added = True
                if topic_type not in topic_rec.usage:
                    usage = topic_rec.usage + topic_type
                    topic_rec.update_record(usage=usage, topic_kind=2)  # topic is simple
            elif topic.sign == "minus" and topic.id in curr_tag_ids:
                q = (db.TblItemTopics.item_type == topic_type) & (db.TblItemTopics.story_id == story_id) & (
                            db.TblItemTopics.topic_id == topic.id)  # got rid of _item_id_
                curr_tag_ids -= set([topic.id])
                # deleted.append(item)
                db(q).delete()
        curr_tags = [all_tags[tag_id] for tag_id in curr_tag_ids]
        keywords = KW_SEP.join(curr_tags)
        changes[doc_id] = dict(keywords=keywords, doc_id=doc_id)
        rec = db(db.TblDocs.id == doc_id).select().first()
        rec = db(db.TblStories.id == rec.story_id).select().first()
        rec.update_record(keywords=keywords, is_tagged=bool(keywords))
        if dates_info:
            update_record_dates(rec, dates_info)
    # changes = [changes[doc_id] for doc_id in sdl]
    # ws_messaging.send_message('DOC-TAGS-CHANGED', group='ALL', changes=changes)
    return dict(new_topic_was_added=new_topic_was_added)


@serve_json
def get_doc_info(vars):
    doc_id = int(vars.doc_id)
    if vars.caller == "stories" or vars.caller == "member":
        q = (db.TblDocs.story_id == doc_id)
    else:
        q = (db.TblDocs.id == doc_id)
    q &= (db.TblStories.id == db.TblDocs.story_id)
    rec = db(q).select().first()
    if not rec:
        raise Exception(f"bad doc_id {doc_id}")
    doc_rec = rec.TblDocs
    doc_id = doc_rec.id
    # doc_story = rec.TblStories
    doc_src = doc_url(None, doc_rec)
    doc_topics = get_object_topics(doc_rec.story_id, "D")
    sm = stories_manager.Stories()
    doc_story = sm.get_story(doc_rec.story_id)
    doc_name = doc_story.name
    all_dates = get_all_dates(doc_story)
    story_id = doc_rec.story_id
    chatroom_id = doc_story.chatroom_id
    member_ids = db(db.TblMembersDocs.doc_id == doc_id).select()
    member_ids = [m.member_id for m in member_ids]
    members = db(db.TblMembers.id.belongs(member_ids)).select()
    members = [Storage(id=member.id,
                       facephotourl=photos_folder(
                           PROFILE_PHOTOS) + (member.facephotourl or "dummy_face.png"),
                       full_name=full_member_name(member))
               for member in members]
    q = (db.TblDocSegments.doc_id == doc_id) & \
        (db.TblDocSegments.story_id == db.TblStories.id) & \
        (db.TblStories.deleted != True)
    doc_segments1 = db(q).select(
        db.TblDocSegments.id,
        db.TblDocSegments.page_num,
        db.TblDocSegments.page_part_num,
        db.TblStories.name,
        db.TblStories.id,
        orderby=db.TblDocSegments.page_num | db.TblDocSegments.page_part_num)
    doc_segments = []
    for doc_segment in doc_segments1:
        seg_members = db(db.TblMembersDocSegments.doc_segment_id ==
                         db.TblDocSegments.id).select()
        seg_member_ids = [
            mem.TblMembersDocSegments.member_id for mem in seg_members]
        item = dict(
            segment_id=doc_segment.TblDocSegments.id,
            page_num=doc_segment.TblDocSegments.page_num,
            page_part_num=doc_segment.TblDocSegments.page_part_num,
            story_id=doc_segment.TblStories.id,
            name=doc_segment.TblStories.name,
            member_ids=seg_member_ids
        )
        doc_segments.append(item)

    return dict(doc=doc_rec,
                doc_id=doc_id,
                doc_src=doc_src,
                doc_name=doc_name,
                doc_story=doc_story,
                doc_topics=doc_topics,
                doc_date_str=all_dates.story_date.date,
                doc_date_datespan=all_dates.story_date.span,
                story_id=story_id,
                chatroom_id=chatroom_id,
                members=members,
                num_pages=doc_rec.num_pages,
                doc_segments1=doc_segments1,
                doc_segments=doc_segments
                )


@serve_json
def get_doc_segment_info(vars):
    doc_segment_id = int(vars.doc_segment_id)
    if vars.caller == "stories" or vars.caller == "member":
        q = (db.TblDocSegments.story_id == doc_segment_id)
    else:
        q = (db.TblDocSegments.id == doc_segment_id)
    q &= (db.TblDocs.id == db.TblDocSegments.doc_id)
    rec = db(q).select().first()
    doc_segment_rec = rec.TblDocSegments;
    doc_segment_id = doc_segment_rec.id  # if it was story id!
    sm = stories_manager.Stories()
    doc_segment_story = sm.get_story(doc_segment_rec.story_id)
    story_id = doc_segment_story.story_id
    chatroom_id = doc_segment_story.chatroom_id
    member_ids = db(db.TblMembersDocSegments.doc_segment_id ==
                    doc_segment_id).select()
    member_ids = [m.member_id for m in member_ids]
    members = db(db.TblMembers.id.belongs(member_ids)).select()
    members = [Storage(id=member.id,
                       facephotourl=photos_folder(
                           PROFILE_PHOTOS) + (member.facephotourl or "dummy_face.png"),
                       full_name=full_member_name(member))
               for member in members]
    doc_topics=get_object_topics(story_id, "S")
    all_dates=get_all_dates(doc_segment_story)
    doc_src=doc_segment_url(None, rec)

    return dict(
        doc_segment=doc_segment_rec,
        doc_id=doc_segment_rec.doc_id,
        doc_src=doc_src,
        members=members,
        name=doc_segment_story.name,
        chatroom_id=chatroom_id,
        story_id=story_id,
        story=doc_segment_story,
        page_num=doc_segment_rec.page_num,
        page_part_num=doc_segment_rec.page_part_num,
        doc_topics=doc_topics,
        doc_seg_date_str=all_dates.story_date.date,
        doc_seg_date_datespan=all_dates.story_date.span
    )


@ serve_json
def create_segment(vars):
    doc_id=vars.doc_id
    if vars.caller == "stories":
        doc_rec=db(db.TblDocs.story_id == doc_id).select().first()
        doc_id=doc_rec.id
    page_num=vars.page_num
    page_part_num=int(vars.page_part_num)
    untitled=vars.untitled
    ppns=("/" + str(page_part_num)) if page_part_num else ""
    story_info=Storage(story_text="---",
                         name=f"{untitled} {page_num}{ppns}",
                         used_for=STORY4DOCSEGMENT,
                         preview="----")
    sm=stories_manager.Stories()
    story_id=sm.add_story(story_info).story_id
    segment_id=db.TblDocSegments.insert(
        doc_id=doc_id, page_num=page_num, page_part_num=page_part_num, story_id=story_id)
    save_doc_segment_thumbnail(segment_id)
    return dict(segment_id=segment_id, name=story_info.name)

@ serve_json
def add_doc_segment(vars):
    doc_id=int(vars.doc_id)
    page_num=int(vars.page_num)
    sm=stories_manager.stories()
    story_id=sm.get_empty_story(used_for=STORY4DOCSEGMENT)
    segment_id=db.TblDocSegments.insert(
        doc_id=doc_id, page_num=page_num, story_id=story_id)
    return dict(segment_id=segment_id)

@ serve_json
def update_doc_date(vars):
    # doc_date_str = vars.doc_date_str
    # doc_dates_info = dict(
    #     doc_date=(vars.doc_date_str, int(vars.doc_date_datespan))
    # )
    # rec = db((db.TblDocs.id == int(vars.doc_id)) & (db.TblDocs.deleted != True)).select().first()
    # update_record_dates(rec, doc_dates_info)
    story_id=int(vars.story_id)
    story_rec=db(db.TblStories.id == story_id).select().first()
    dates_info=dict(
        story_date=(vars.doc_date_str, int(vars.doc_date_datespan))
    )
    update_record_dates(story_rec, dates_info)
    return dict()


@ serve_json
def update_doc_members(vars):
    doc_id=int(vars.doc_id)
    old_members=db(db.TblMembersDocs.doc_id == doc_id).select()
    old_members=[m.member_id for m in old_members]
    old_members_set=set(old_members)
    new_members=vars.member_ids
    new_members_set=set(new_members)
    deleted_members=[mid for mid in old_members if mid not in new_members_set]
    q=(db.TblMembersDocs.doc_id == doc_id) & (
        db.TblMembersDocs.member_id.belongs(deleted_members))
    db(q).delete()
    for mid in new_members:
        if mid not in old_members_set:
            db.TblMembersDocs.insert(doc_id=doc_id, member_id=mid)
    members=db(db.TblMembers.id.belongs(new_members)).select(
        db.TblMembers.id, db.TblMembers.facephotourl)
    for member in members:
        member.facephotourl=photos_folder(
            PROFILE_PHOTOS) + (member.facephotourl or "dummy_face.png")
    return dict(members=members)

@ serve_json
def update_doc_segment_members(vars):
    doc_segment_id=int(vars.doc_segment_id)
    old_members=db(db.TblMembersDocSegments.doc_segment_id ==
                   doc_segment_id).select()
    old_member_ids=[m.member_id for m in old_members]
    old_members_set=set(old_member_ids)
    new_members=vars.member_ids
    new_members_set=set(new_members)
    # deleted_members=[mid for mid in old_members if mid not in new_members_set]
    # does not work. Python bug?
    deleted_members = []
    for mid in old_member_ids:
        if mid not in new_members_set:
            deleted_members.append(mid)
    q=(db.TblMembersDocSegments.doc_segment_id == doc_segment_id) & (
        db.TblMembersDocSegments.member_id.belongs(deleted_members))
    db(q).delete()
    for mid in new_members:
        if mid not in old_members_set:
            db.TblMembersDocSegments.insert(
                doc_segment_id=doc_segment_id, member_id=mid)
    members=db(db.TblMembers.id.belongs(new_members)).select(
        db.TblMembers.id, db.TblMembers.facephotourl)
    for member in members:
        member.facephotourl=photos_folder(
            PROFILE_PHOTOS) + (member.facephotourl or "dummy_face.png")
    return dict(members=members)

@ serve_json
def update_story_preview(vars):
    story_id=int(vars.story_id)
    story_rec=db(db.TblStories.id == story_id).select().first()
    story_rec.update_record(preview=story_rec.preview)
    return dict()

@ serve_json
def remove_doc_segment(vars):
    doc_segment_id=vars.doc_segment_id
    ds_rec=db(db.TblDocSegments.id == doc_segment_id).select().first()
    story_deleted=False
    if ds_rec.story_id:
        db(db.TblStories.id == ds_rec.story_id).update(deleted=True)
        story_deleted=True
    return dict(story_deleted=story_deleted)

# ----------------support functions-----------------

def make_docs_query(params):
    q=init_query(db.TblDocs, params.editing)
    if params.days_since_upload:
        days=params.days_since_upload.value
        if days:
            upload_date=datetime.datetime.today() - datetime.timedelta(days=days)
            q &= (db.TblDocs.upload_date >= upload_date)
    opt=params.selected_uploader
    if opt == 'mine':
        q &= (db.TblDocs.uploader == params.user_id)
    elif opt == 'users':
        q &= (db.TblDocs.uploader != None)
    opt=params.selected_dates_option
    if opt == 'selected_dates_option':
        pass
    elif opt == 'dated':
        q &= (db.TblDocs.doc_date != NO_DATE)
    elif opt == 'undated':
        q &= (db.TblDocs.doc_date == NO_DATE)
    if params.selected_docs:
        q &= (db.TblDocs.story_id.belongs(params.selected_docs))
    if params.selected_topics:
        q1=get_topics_query(params.selected_topics)
        q &= q1
    if params.show_untagged:
        q &= (db.TblDocs.story_id == db.TblStories.id) & (
            db.TblStories.is_tagged == False)
    q &= (db.TblDocs.crc != None)
    return q

def make_doc_segments_query(params):
    q=init_query(db.TblDocSegments, params.editing)
    q &= (db.TblDocs.id == db.TblDocSegments.doc_id)
    if params.days_since_upload:
        days=params.days_since_upload.value
        if days:
            upload_date=datetime.datetime.today() - datetime.timedelta(days=days)
            q &= (db.TblDocs.upload_date >= upload_date)
    opt=params.selected_uploader
    if opt == 'mine':
        q &= (db.TblDocs.uploader == params.user_id)
    elif opt == 'users':
        q &= (db.TblDocs.uploader != None)
    opt=params.selected_dates_option
    if opt == 'selected_dates_option':
        pass
    elif opt == 'dated':
        q &= (db.TblDocs.doc_date != NO_DATE)
    elif opt == 'undated':
        q &= (db.TblDocs.doc_date == NO_DATE)
    if params.selected_doc_segments:
        q &= (db.TblDocSegments.story_id.belongs(params.selected_doc_segments))
    if params.selected_topics:
        q1=get_topics_query(params.selected_topics)
        q &= q1
    if params.show_untagged:
        q &= (db.TblDocSegments.story_id == db.TblStories.id) & (
            db.TblStories.is_tagged == False)
    return q

def get_story_by_id(story_id):
    sm=stories_manager.Stories()
    return sm.get_story(story_id)


@ serve_json
def upload_thumbnail(vars):
    info=vars.file.info
    doc_id=info.doc_id
    ptp_key=info.ptp_key
    segment_id=info.segment_id
    keys=info.keys()
    fil=vars.file
    result=save_uploaded_thumbnail(fil.BINvalue, doc_id, segment_id, ptp_key)
    return dict(upload_result=result)

def full_member_name(member):
    s = member.first_name or ""
    if member.last_name:
        s += " " + member.last_name
    return s
