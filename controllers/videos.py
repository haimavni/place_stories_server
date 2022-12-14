import ws_messaging
import datetime
import random
import re

import stories_manager
import ws_messaging
from date_utils import update_record_dates, fix_record_dates_in, fix_record_dates_out
from folders import url_video_folder
from members_support import *


@serve_json
def save_video(vars):
    # https://photos.app.goo.gl/TndZ4fgyih57pmzS6 - shared google photos
    user_id = vars.user_id
    params = vars.params
    date_info = dict(video_date=(params.video_date_datestr, params.video_date_datespan))
    if not params.id:  # creation, not modification
        pats = dict(
            youtube=r'https://(?:www.youtube.com/watch\?v=|youtu\.be/)(?P<code>[^&]+)',
            html5=r'(?P<code>.+\.mp4)',
            vimeo=r'https://vimeo.com/(?P<code>\d+)',
            google_drive=r'https://drive.google.com/file/d/(?P<code>[^/]+?)/.*',
            google_photos=r'https://photos.app.goo.gl/(?P<code>[^&]+)'
        )
        src = None
        for t in pats:
            pat = pats[t]
            m = re.search(pat, params.src)
            if m:
                src = m.groupdict()['code']
                typ = t
                break
        if not src:
            raise User_Error('!videos.unknown-video-type')
        q = (db.TblVideos.src == src) & \
            (db.TblVideos.video_type == typ) & \
            (db.TblVideos.deleted != True)
        if db(q).count() > 0:
            raise User_Error('!videos.duplicate')
        sm = stories_manager.Stories()
        story_info = sm.get_empty_story(used_for=STORY4VIDEO, story_text="", name=params.name)
        result = sm.add_story(story_info)
        story_id = result.story_id
        data = dict(
            video_type=typ,
            name=params.name,
            src=src,
            story_id=story_id,
            contributor=user_id,
            upload_date=datetime.datetime.now()
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
        # data = dict()
        # for fld in old_rec:
        # if fld in ('src', 'update_record', 'delete_record'):
        # continue
        # if old_rec[fld] != params[fld]:
        # data[fld] = params[fld]
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
        keywords = "; ".join(curr_tags)
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
    lst1 = [dict(src=rec.src,video_id=rec.id, name=rec.name) for rec in lst1]
    q2 = q & (db.TblVideos.touch_time == NO_DATE)
    lst2 = db(q2).select(limitby=(0, 200))
    lst2 = [dict(src=rec.src,video_id=rec.id, name=rec.name) for rec in lst2]
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
                       facePhotoURL=photos_folder('profile_photos') + (member.facePhotoURL or "dummy_face.png"),
                       full_name=member.first_name + ' ' + member.last_name) for member in members]
    return dict(video_source=video_source,
                video_story=video_story,
                video_id=video_id,
                photographer_name=photographer_name,
                photographer_id=photographer_id,
                video_date_str = all_dates.video_date.date,
                photo_date_datespan = all_dates.video_date.span,
                video_topics=video_topics,
                members=members,
                cue_points=cue_points)

@serve_json
def update_video_cue_points(vars):
    video_id = int(vars.video_id)
    old_cp = db(db.TblVideoCuePoints.video_id==video_id).select()
    old_cp_set = set([cp.time for cp in old_cp])
    new_cp_set = set([cp.time for cp in vars.cue_points])
    dic = dict()
    for cp in vars.cue_points:
        dic[cp.time] = cp.description
    for t in old_cp_set:
        if t not in new_cp_set:
            db((db.TblVideoCuePoints.video_id == video_id)&(db.TblVideoCuePoints.time == t)).delete()
    for t in new_cp_set:
        if t in old_cp_set:
            db((db.TblVideoCuePoints.video_id == video_id) & (db.TblVideoCuePoints.time == t)).update(description=dic[t])
        else:
            db.TblVideoCuePoints.insert(time=t, description=dic[t], video_id=video_id)
    return dict()

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
    members = db(db.TblMembers.id.belongs(new_members)).select(db.TblMembers.id, db.TblMembers.facePhotoURL)
    for member in members:
        member.facePhotoURL = photos_folder('profile_photos') + (member.facePhotoURL or "dummy_face.png")
    return dict(members=members)

@serve_json
def update_cue_members(vars):
    video_id = int(vars.video_id)
    time = int(vars.time)
    member_ids = vars.member_ids
    old_member_ids = calc_cue_members(video_id, time)
    q = (db.TblVideoCuePoints.video_id == video_id) & \
        (db.TblVideoCuePoints.time == time)
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
    members = db(db.TblMembersVideos.video_id==video_id).select(db.TblMembers.id, db.TblMembers.facePhotoURL)
    return dict(members=members)

@serve_json
def video_cue_points(vars):
    cue_points = calc_cue_points(vars.video_id)
    return dict(cue_points=cue_points)

def calc_cue_members(video_id, time):
    q = (db.TblMembersVideoCuePoints.cue_point_id == db.TblVideoCuePoints.id) & \
        (db.TblVideoCuePoints.video_id == video_id) & \
        (db.TblVideoCuePoints.time == time)
    lst = db(q).select()
    member_ids = [rec.TblMembersVideoCuePoints.member_id for rec in lst]
    return member_ids

def calc_cue_points(video_id):
    q = (db.TblVideoCuePoints.video_id == video_id)
    lst = db(q).select(orderby=db.TblVideoCuePoints.time)
    cue_points = [dict(time=rec.time, description=rec.description, member_ids=calc_cue_members(video_id, rec.time)) for rec in lst]
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
