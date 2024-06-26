import ws_messaging
import datetime
import random
import re

import stories_manager
import ws_messaging
from date_utils import update_record_dates, fix_record_dates_in, fix_record_dates_out
from folders import url_video_folder
from members_support import *
from video_support import upgrade_youtube_info, update_cuepoints_text, parse_video_url, youtube_info, save_uploaded_video_thumbnail
from folders import RESIZED, ORIG, SQUARES, PROFILE_PHOTOS
from gluon.storage import Storage

@serve_json
def save_video(vars):
    # https://photos.app.goo.gl/TndZ4fgyih57pmzS6 - shared google photos
    user_id = vars.user_id
    params = vars.params
    date_info = dict(video_date=(params.video_date_datestr, params.video_date_datespan))
    if not params.id:  # creation, not modification
        vidi = parse_video_url(params.src)
        q = (db.TblVideos.src == vidi.src) & \
            (db.TblVideos.video_type == vidi.video_type) & \
            (db.TblVideos.deleted != True)
        if db(q).count() > 0:
            raise User_Error('!videos.duplicate')
        sm = stories_manager.Stories()
        story_info = sm.get_empty_story(used_for=STORY4VIDEO, story_text="", name=params.name)
        result = sm.add_story(story_info)
        story_id = result.story_id
        yt_info = youtube_info(vidi.src) if vidi.video_type == "youtube" else Storage(thumbnail_url=vars.thumbnail_src, allow="encrypted-media")
        data = dict(
            video_type=vidi.video_type,
            name=params.name,
            src=vidi.src,
            story_id=story_id,
            contributor=user_id,
            upload_date=datetime.datetime.now(),
            thumbnail_url=yt_info.thumbnail_url,
            description=yt_info.description,
            uploader=yt_info.uploader,
            duration=yt_info.duration,
            yt_upload_date=yt_info.upload_date,
            allow=yt_info.allow
        )
        vid = db.TblVideos.insert(**data)
        data.update(id=vid)
        if params.video_date_datestr:
            rec = db(db.TblVideos.id == vid).select().first()
            date_data = dict(
                video_date_datestr=params.video_date_datestr,
                video_date_datespan=params.video_date_span
            )
            date_data_in = fix_record_dates_in(rec, date_data)
            rec.update_record(**date_data_in)
            data.update(
                video_date_datestr=params.video_date_datestr,
                video_date_datespan=params.video_date_datespan)
        else:
            data.update(video_date_datestr='1', video_date_datespan=0)
        ###update_record_dates(rec, date_info)
        ws_messaging.send_message(key='NEW-VIDEO', group='ALL', new_video_rec=data)
    else:
        old_rec = db(db.TblVideos.id == params.id).select().first()
        vid = old_rec.id
        del params['src']  #
        data = params
        if data:
            data_in = fix_record_dates_in(old_rec, data)
            old_rec.update_record(**data_in)
            update_record_dates(old_rec, date_info)
            if 'name' in data:
                sm = stories_manager.Stories()
                story_info = sm.get_story(old_rec.story_id)
                story_info.name = params.name
                sm.update_story(old_rec.story_id, story_info)
                ws_messaging.send_message(key='VIDEO-INFO-CHANGED', group='ALL', changes=data)
    return dict(video_id=vid)


@serve_json
def delete_videos(vars):
    selected_videos = vars.selected_videos
    sm = stories_manager.Stories()
    selected_videos=selected_videos.split(',')
    selected_videos = [int(vid) for vid in selected_videos]
    for vid in selected_videos:
        story_id = db(db.TblVideos.id == vid).select().first().story_id
        sm.delete_story(story_id)
    db(db.TblVideos.id.belongs(selected_videos)).update(deleted=True)
    return dict()

@serve_json
def refresh_video_thumbnails(vars):
    selected_videos = vars.selected_videos
    result = upgrade_youtube_info(video_list=selected_videos)
    return result

@serve_json
def get_video_list(vars):
    q = make_videos_query(vars)
    lst = db(q).select()
    selected_video_list = vars.selected_video_list
    q = (db.TblVideos.id.belongs(selected_video_list)) & (db.TblStories.id == db.TblVideos.story_id)
    if selected_video_list:
        lst1 = db(q).select()
        lst1 = [rec for rec in lst1]
        for rec in lst1:
            rec.TblVideos.selected = True
    else:
        lst1 = []
    lst1_ids = [rec.TblVideos.id for rec in lst1]
    lst = [rec for rec in lst if rec.TblVideos.id not in lst1_ids]
    lst = lst1 + lst
    ##lst = db(db.TblVideos.deleted != True).select()
    video_list = []
    for rec1 in lst:
        rec = rec1.TblVideos
        fix_record_dates_out(rec)
        rec.keywords = rec1.TblStories.keywords
        video_list.append(rec)
    return dict(video_list=video_list)


@serve_json
def apply_to_selected_videos(vars):
    all_tags = calc_all_tags()
    svl = vars.selected_video_list
    plist = vars.selected_photographers
    if len(plist) == 1:
        photographer_id = plist[0].option.id
    else:
        photographer_id = None
    if vars.photos_date_str:
        dates_info = dict(
            photo_date=(vars.photos_date_str, vars.photos_date_span_size)
        )
    else:
        dates_info = None

    st = vars.selected_topics
    added = []
    deleted = []
    changes = dict()
    new_topic_was_added = False
    for vid in svl:
        vrec = db(db.TblVideos.id == vid).select().first()
        story_id = vrec.story_id if vrec else None
        curr_tag_ids = set(get_tag_ids(story_id, "V"))
        for tpc in st:
            topic = tpc.option
            item = dict(story_id=story_id, topic_id=topic.id)
            if topic.sign == "plus" and topic.id not in curr_tag_ids:
                if not story_id:
                    continue
                new_id = db.TblItemTopics.insert(
                    item_type="V",
                    topic_id=topic.id,
                    story_id=story_id)
                curr_tag_ids |= set([topic.id])
                added.append(item)
                topic_rec = db(db.TblTopics.id == topic.id).select().first()
                if topic_rec.topic_kind == 0:  # never used
                    new_topic_was_added = True
                if 'V' not in topic_rec.usage:
                    usage = topic_rec.usage + 'V'
                    topic_rec.update_record(usage=usage, topic_kind=2)  # simple topic
            elif topic.sign == "minus" and topic.id in curr_tag_ids:
                q = (db.TblItemTopics.item_type == "V") & \
                    (db.TblItemTopics.story_id == story_id) & \
                    (db.TblItemTopics.topic_id == topic.id)
                curr_tag_ids -= set([topic.id])
                deleted.append(item)
                db(q).delete()
        curr_tags = [all_tags[tag_id] for tag_id in curr_tag_ids]
        keywords = KW_SEP.join(curr_tags)
        changes[vid] = dict(keywords=keywords, video_id=vid)
        rec = db(db.TblVideos.id == vid).select().first()
        rec1 = db(db.TblStories.id == rec.story_id).select().first()
        rec1.update_record(keywords=keywords, is_tagged=bool(keywords))
        if photographer_id:
            rec.update_record(photographer_id=photographer_id)
            rec1 = db(db.TblPhotographers.id == photographer_id).select().first()
            kind = rec1.kind or ''
            if not 'V' in kind:
                kind += 'V'
                rec1.update_record(kind=kind)
            changes[vid]['photographer_name'] = rec1.name
            changes[vid]['photographer_id'] = photographer_id
        if dates_info:
            update_record_dates(rec, dates_info)
    changes = [changes[vid] for vid in svl]
    ws_messaging.send_message('VIDEO-TAGS-CHANGED', group='ALL', changes=changes)
    return dict(new_topic_was_added=new_topic_was_added)


@serve_json
def promote_videos(vars):
    selected_video_list = vars.params.selected_video_list
    q = (db.TblVideos.id.belongs(selected_video_list))
    today = datetime.date.today()
    db(q).update(touch_time=today)
    return dict()

@serve_json
def assign_video_photographer(vars):
    video_id = int(vars.video_id)
    photographer_id = int(vars.photographer_id) if vars.photographer_id else None
    db(db.TblVideos.id==video_id).update(photographer_id=photographer_id)
    return dict()

@serve_json
def get_video_sample(vars):
    q = (db.TblVideos.deleted == False)
    q1 = q & (db.TblVideos.touch_time != NO_DATE)
    lst1 = db(q1).select(limitby=(0, 10), orderby=~db.TblVideos.touch_time)
    lst1 = [dict(src=rec.src,video_id=rec.id, name=rec.name, thumbnail_url=rec.thumbnail_url) for rec in lst1]
    q2 = q & (db.TblVideos.touch_time == NO_DATE)
    lst2 = db(q2).select(limitby=(0, 200))
    lst2 = [dict(src=rec.src,video_id=rec.id, name=rec.name, thumbnail_url=rec.thumbnail_url) for rec in lst2]
    if len(lst2) > 10:
        lst2 = random.sample(lst2, 10)
    lst = lst1 + lst2
    return dict(video_list=lst)

@serve_json
def update_video_date(vars):
    video_dates_info = dict(
        video_date = (vars.video_date_str, int(vars.video_date_datespan))
    )
    vrec = db((db.TblVideos.id==int(vars.video_id)) & (db.TblVideos.deleted != True)).select().first()
    update_record_dates(vrec, video_dates_info)
    return dict()


@serve_json
def get_video_info(vars):
    video_id = int(vars.video_id)
    if vars.by_story_id:
        vrec = db(db.TblVideos.story_id==video_id).select().first()
        video_id = vrec.id
    else:
        vrec = db(db.TblVideos.id==video_id).select().first()
    video_source = vrec.src
    video_url = calc_video_url(vrec.video_type, video_source)
    if vars.cuepoints_enabled:
        cue_points = calc_cue_points(video_id)
    else:
        cue_points = []
    sm = stories_manager.Stories()
    video_story=sm.get_story(vrec.story_id)
    photographer = db(db.TblPhotographers.id==vrec.photographer_id).select().first() if vrec.photographer_id else None
    photographer_name = photographer.name if photographer else ''
    photographer_id = photographer.id if photographer else None
    video_topics = get_video_topics(vrec.story_id)
    all_dates = get_all_dates(vrec)
    member_ids = db(db.TblMembersVideos.video_id==video_id).select()
    member_ids = [m.member_id for m in member_ids]
    members = db(db.TblMembers.id.belongs(member_ids)).select()
    members = [Storage(id=member.id,
                       facephotourl=photos_folder(PROFILE_PHOTOS) + (member.facephotourl or "dummy_face.png"),
                       full_name=get_full_name(member)) for member in members]
    return dict(video_source=video_source,
                video_url=video_url,
                video_story=video_story,
                video_id=video_id,
                photographer_name=photographer_name,
                photographer_id=photographer_id,
                video_date_str = all_dates.video_date.date,
                photo_date_datespan = all_dates.video_date.span,
                video_topics=video_topics,
                members=members,
                thumbnail_url=vrec.thumbnail_url,
                allow="encrypted-media",
                cue_points=cue_points)

def get_full_name(member):
    result = ""
    if member.first_name:
        result += member.first_name
    if member.last_name:
        if result:
            result += " "
        result += member.last_name
    return result

def calc_video_url(video_type, video_src):
    if video_type == "youtube":
        return "https://www.youtube.com/embed/" + video_src + "?wmode=opaque"
    if video_type == "raw":
        return video_src;
    raise Exception(video_type + " not ready yet")

@serve_json
def update_video_cue_points(vars):
    video_id = int(vars.video_id)
    old_cp = db(db.TblVideoCuePoints.video_id==video_id).select()
    old_cp_set = set([cp.id for cp in old_cp])
    new_cp_set = set([cp.cue_id for cp in vars.cue_points])
    added_cue_points = dict()
    new_id = None
    dic = dict()
    for cp in vars.cue_points:
        dic[cp.cue_id] = [cp.time, cp.description]
    for cid in old_cp_set:
        if cid not in new_cp_set:
            db((db.TblVideoCuePoints.video_id == video_id)&(db.TblVideoCuePoints.id == cid)).delete()
    for cid in new_cp_set:
        if cid in old_cp_set:
            db((db.TblVideoCuePoints.video_id == video_id) & (db.TblVideoCuePoints.id == cid)). \
                update(time=dic[cid][0], description=dic[cid][1])
        else:
            tim = dic[cid][0]
            new_id = db.TblVideoCuePoints.insert(time=tim, description=dic[cid][1], video_id=video_id)
            # comment(f"new cue {new_id} was created in update video cue points")
            added_cue_points[tim] = new_id
    story_id = db(db.TblVideos.id==video_id).select().first().story_id
    update_cuepoints_text(video_id);
    invalidate_index(story_id)
    return dict(cue_id=new_id)

@serve_json
def update_video_members(vars):
    video_id = int(vars.video_id)
    old_members = db(db.TblMembersVideos.video_id==video_id).select()
    old_members = [m.member_id for m in old_members]
    old_members_set = set(old_members)
    new_members = vars.member_ids
    new_members_set = set(new_members)
    deleted_members = [mid for mid in old_members if mid not in new_members_set]
    q = (db.TblMembersVideos.video_id==video_id) & (db.TblMembersVideos.member_id.belongs(deleted_members))
    db(q).delete()
    for mid in new_members:
        if mid not in old_members_set:
            db.TblMembersVideos.insert(video_id=video_id, member_id=mid)
    members = db(db.TblMembers.id.belongs(new_members)).select(db.TblMembers.id, db.TblMembers.facephotourl)
    for member in members:
        member.facephotourl = photos_folder(PROFILE_PHOTOS) + (member.facephotourl or "dummy_face.png")
    return dict(members=members)

@serve_json
def update_cue_members(vars):
    video_id = int(vars.video_id)
    cid = int(vars.cue_id)
    # if not cid:
    #     cid = db.TblVideoCuePoints.insert(video_id=video_id, time=vars.time, description=vars.description, member_ids=vars.member_ids)
    #     comment(f"updating members, new cid created {cid}")
    member_ids = vars.member_ids
    old_member_ids = calc_cue_members(video_id, cid)
    q = (db.TblVideoCuePoints.id == cid)
    rec = db(q).select().first()
    cue_id = rec.id
    for mem_id in old_member_ids:
        if mem_id not in member_ids:
            q = (db.TblMembersVideoCuePoints.cue_point_id==cue_id) & \
                (db.TblMembersVideoCuePoints.member_id == mem_id)
            db(q).delete()
            #update link between members and video
            q = (db.TblMembersVideos.member_id==mem_id) & (db.TblMembersVideos.video_id==video_id)
            vmrec = db(q).select().first()
            if vmrec.cuepoints_count==1:
                db(q).delete()
            else:
                vmrec.update_record(cuepoints_count=vmrec.cuepoints_count-1)
    for mem_id in member_ids:
        if mem_id not in old_member_ids:
            db.TblMembersVideoCuePoints.insert(member_id=mem_id, cue_point_id=cue_id)
            #update link between members and video
            q = (db.TblMembersVideos.member_id==mem_id) & (db.TblMembersVideos.video_id==video_id)
            vmrec = db(q).select().first()
            if vmrec:
                vmrec.update_record(cuepoints_count=vmrec.cuepoints_count+1)
            else:
                db.TblMembersVideos.insert(member_id=mem_id, video_id=video_id, cuepoints_count=1)
    return dict(cue_id=cue_id)

@serve_json
def video_cue_points(vars):
    cue_points = calc_cue_points(vars.video_id)
    return dict(cue_points=cue_points)

@serve_json
def replace_thumbnail_url(vars):
    video_id = int(vars.video_id)
    video_rec = db(db.TblVideos.id==video_id).select().first()
    video_rec.update_record(thumbnail_url=vars.thumbnail_url)
    return dict()

def calc_cue_members(video_id, cue_id):
    q = (db.TblMembersVideoCuePoints.cue_point_id == db.TblVideoCuePoints.id) & \
        (db.TblVideoCuePoints.video_id == video_id) & \
        (db.TblVideoCuePoints.id == cue_id)
    lst = db(q).select()
    member_ids = [rec.TblMembersVideoCuePoints.member_id for rec in lst]
    return member_ids

def calc_cue_points(video_id):
    q = (db.TblVideoCuePoints.video_id == video_id)
    lst = db(q).select(orderby=db.TblVideoCuePoints.time)
    cue_points = [dict(
        cue_id=rec.id, 
        time=rec.time, 
        description=rec.description, 
        member_ids=calc_cue_members(video_id, rec.id)
        ) for rec in lst]
    return cue_points


def make_videos_query(vars):
    q = init_query(db.TblVideos, editing=vars.editing)
    ###q = (db.TblVideos.deleted != True)
    photographer_list = [p.option.id for p in vars.selected_photographers] \
        if vars.selected_photographers else []
    if len(photographer_list) > 0:
        q &= db.TblVideos.photographer_id.belongs(photographer_list)
    if vars.selected_days_since_upload:
        days = vars.selected_days_since_upload.value
        if days:
            upload_date = datetime.datetime.today() - datetime.timedelta(days=days)
            q &= (db.TblVideos.upload_date >= upload_date)
    opt = vars.selected_uploader
    if opt == 'mine':
        q &= (db.TblVideos.uploader == vars.user_id)
    elif opt == 'users':
        q &= (db.TblVideos.uploader != None)
    opt = vars.selected_dates_option
    if opt == 'selected_dates_option':
        pass
    elif opt == 'dated':
        q &= (db.TblVideos.video_date != NO_DATE)
    elif opt == 'undated':
        q &= (db.TblVideos.video_date == NO_DATE)
    if vars.selected_topics:
        q1 = get_topics_query(vars.selected_topics)
        q &= q1
    if vars.show_untagged:
        q &= (db.TblVideos.story_id==db.TblStories.id) & (db.TblStories.is_tagged==False)
    return q

def get_video_topics(story_id):
    db = inject('db')
    q = (db.TblItemTopics.story_id == story_id) & (db.TblItemTopics.item_type == 'V') & (
                db.TblTopics.id == db.TblItemTopics.topic_id)
    lst = db(q).select()
    lst = [itm.TblTopics.as_dict() for itm in lst]
    for itm in lst:
        itm['sign'] = ""
    lst = make_unique(lst, 'id')
    return lst

@serve_json
def story_id_to_video_id(vars):
    id = vars.id
    vrec = db(db.TblVideos.story_id==id).select().first()
    return dict(video_id=vrec.id)

def invalidate_index(story_id):
    story_rec = db(db.TblStories.id==story_id).select().first()
    story_rec.update_record(indexing_date=NO_DATE, last_update_date=request.now)
    
@ serve_json
def upload_video_thumbnail(vars):
    comment("-----------------enter upload doc thumbnail.")
    info=vars.file.info
    video_id=info.video_id
    ptp_key=info.ptp_key
    fil=vars.file
    result=save_uploaded_video_thumbnail(fil.BINvalue, video_id, ptp_key)
    return dict(upload_result=result)

    