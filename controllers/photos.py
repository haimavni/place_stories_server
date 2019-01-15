from photos_support import photos_folder, local_photos_folder, images_folder, local_images_folder, save_uploaded_photo, rotate_photo, save_member_face
import ws_messaging
import stories_manager
from date_utils import date_of_date_str, parse_date, get_all_dates, update_record_dates, fix_record_dates_in, fix_record_dates_out
from members_support import *
import random
import datetime
import os

@serve_json
def upload_photo(vars):
    user_id = vars.user_id or auth.current_user()
    comment("start handling uploaded files")
    user_id = int(vars.user_id) if vars.user_id else auth.current_user()
    fil = vars.file
    result = save_uploaded_photo(fil.name, fil.BINvalue, user_id)
    return dict(upload_result=result)

@serve_json
def get_photo_detail(vars):
    photo_id = int(vars.photo_id)
    if vars.what == 'story': #This photo is identified by the associated story
        rec = db(db.TblPhotos.story_id==photo_id).select().first()
    else:
        rec = db(db.TblPhotos.id==photo_id).select().first()
    sm = stories_manager.Stories()
    story=sm.get_story(rec.story_id)
    if not story:
        story = sm.get_empty_story(used_for=STORY4PHOTO)
    all_dates = get_all_dates(rec)        
    return dict(photo_src=photos_folder() + rec.photo_path,
                photo_name=rec.Name,
                height=rec.height,
                width=rec.width,
                photo_story=story,
                photo_date_str = all_dates.photo_date.date,
                photo_date_datespan = all_dates.photo_date.span,
                photo_id=rec.id)

@serve_json
def update_photo_caption(vars):
    photo_id = int(vars.photo_id)
    caption = vars.caption
    photo_rec = db(db.TblPhotos.id==photo_id).select().first()
    photo_rec.update(Name=caption)
    sm = stories_manager.Stories()
    sm.update_story_name(photo_rec.story_id, caption)
    return dict(bla='bla')

@serve_json
def update_photo_date(vars):
    photo_date_str = vars.photo_date_str
    photo_dates_info = dict(
        photo_date = (vars.photo_date_str, int(vars.photo_date_datespan))
    )
    rec = db(db.TblPhotos.id==int(vars.photo_id)).select().first()
    update_record_dates(rec, photo_dates_info)
    #todo: save in db
    return dict()

@serve_json
def get_photo_info(vars):
    photo_id = int(vars.photo_id)
    rec = db(db.TblPhotos.id==photo_id).select().first()
    all_dates = get_all_dates(rec)
    if rec.photographer_id:
        photographer_rec = db(db.TblPhotographers.id==rec.photographer_id).select().first()
    else:
        photographer_rec = Storage()
    result = dict(
        name=rec.Name,
        description=rec.Description,
        photographer=photographer_rec.name,
        photo_date_str = all_dates.photo_date.date,
        photo_date_datespan = all_dates.photo_date.span,
        photo_date_dateunit = all_dates.photo_date.unit
    )
    return result

@serve_json
def save_photo_info(vars):
    pi = vars.photo_info
    ###pi.photographer_id = find_or_insert(pi.photographer)
    unit, date = parse_date(pi.photo_date_str)
    photo_rec = db(db.TblPhotos.id==vars.photo_id).select().first()
    if pi.name != photo_rec.Name:
        sm = stories_manager.Stories(vars.user_id)
        sm.update_story_name(photo_rec.story_id, pi.name)
    del pi.photo_date_str
    pi.photo_date = date
    pi.photo_date_dateunit = unit
    del pi.photographer
    pi.Name = pi.name
    del pi.name
    photo_rec.update_record(**pi)
    return dict()

@serve_json
def get_faces(vars):
    photo_id = vars.photo_id;
    lst = db(db.TblMemberPhotos.Photo_id==photo_id).select()
    faces = []
    candidates = []
    for rec in lst:
        if rec.r == None: #found old record which has a member but no location
            if not rec.Member_id:
                db(db.TblMemberPhotos.id==rec.id).delete()
                continue
            name = member_display_name(member_id=rec.Member_id)
            candidate = dict(member_id=rec.Member_id, name=name)
            candidates.append(candidate)
        else:
            face = Storage(x = rec.x, y=rec.y, r=rec.r or 20, photo_id=rec.Photo_id)
            if rec.Member_id:
                face.member_id = rec.Member_id
                face.name = member_display_name(member_id=rec.Member_id)
            faces.append(face)
    face_ids = set([face.member_id for face in faces])
    candidates = [c for c in candidates if not c['member_id'] in face_ids]
    return dict(faces=faces, candidates=candidates)

@serve_json
def save_face(vars):
    return save_member_face(vars)

@serve_json
def detach_photo_from_member(vars):
    member_id = vars.member_id
    photo_id = vars.photo_id
    q = (db.TblMemberPhotos.Photo_id==photo_id) & \
        (db.TblMemberPhotos.Member_id==member_id)
    good = db(q).delete() == 1
    return dict(photo_detached=good)

@serve_json
def get_photo_list(vars):
    selected_topics = vars.selected_topics or []
    mprl = vars.max_photos_per_line or 8;
    MAX_PHOTOS_COUNT = 100 + (mprl - 8) * 100
    if selected_topics:
        lst = get_photo_list_with_topics(vars)
    else:
        q = make_photos_query(vars)
        n = db(q).count()
        if n > MAX_PHOTOS_COUNT:
            frac = max(MAX_PHOTOS_COUNT * 100 / n, 1)
            sample = random.sample(range(1, 101), frac)
            ##q &= (db.TblPhotos.random_photo_key <= frac)
            q &= (db.TblPhotos.random_photo_key.belongs(sample)) #we don't want to bore our uses so there are several collections
        lst = db(q).select() ###, db.TblPhotographers.id) ##, db.TblPhotographers.id)
        if lst and 'TblMemberPhotos' in lst[0]:
            lst = [rec.TblPhotos for rec in lst]
    if len(lst) > MAX_PHOTOS_COUNT:
        lst1 = random.sample(lst, MAX_PHOTOS_COUNT)
        lst = lst1
    selected_photo_list = vars.selected_photo_list
    result = []
    if selected_photo_list:
        lst1 = db(db.TblPhotos.id.belongs(selected_photo_list)).select()
        lst1 = [rec for rec in lst1]
        for rec in lst1:
            rec.selected = 'photo-selected'
    else:
        lst1 = []
    lst1_ids = [rec.id for rec in lst1]
    lst = [rec for rec in lst if rec.id not in lst1_ids]
    lst = lst1 + lst
    for rec in lst:
        dic = dict(
            keywords = rec.KeyWords or "",
            description = rec.Description or "",
            name = rec.Name,
            title='{}: {}'.format(rec.Name, rec.KeyWords),
            square_src = photos_folder('squares') + rec.photo_path,
            src=photos_folder('orig') + rec.photo_path,
            photo_id=rec.id,
            width=rec.width,
            height=rec.height,
            selected=rec.selected if 'selected' in rec else ''
        )
        result.append(dic)
    return dict(photo_list=result)

@serve_json    
def get_theme_data(vars):
    path = images_folder()
    local_path = local_images_folder()
    files = dict(
        header_background='header-background.png',
        top_background='top-background.png',
        footer_background='footer-background.png',
        founders_group_photo='founders_group_photo.jpg',
        app_logo='app-logo.png',
        himnon='himnon-givat-brenner.mp3',
        content_background='bgs/body-bg.jpg',
        mayflower='bgs/mayflower.jpg'
    )
    result = dict()
    for k in files:
        result[k] = path + files[k] if os.path.exists(local_path + files[k]) else ''
        if not os.path.exists(local_path + files[k]):
            comment("file {} is missing", k)                   
    return dict(files=result)

@serve_json
def apply_to_selected_photos(vars):
    all_tags = calc_all_tags()
    spl = vars.selected_photo_list
    plist = vars.selected_photographers
    if len(plist) == 1:
        photographer_id = plist[0].option.id
    else:
        photographer_id = None
    photos_date_str = vars.photos_date_str
    if photos_date_str:
        dates_info = dict(
            photo_date = (photos_date_str, vars.photos_date_span_size)
        )
    else:
        dates_info = None

    st = vars.selected_topics
    added = []
    deleted = []
    for pid in spl:
        curr_tag_ids = set(get_tag_ids(pid, "P"))
        for tpc in st:
            topic = tpc.option
            item = dict(item_id=pid, topic_id=topic.id)
            if topic.sign=="plus" and topic.id not in curr_tag_ids:
                rec = db(db.TblPhotos.id==pid).select().first()
                story_id = rec.story_id if rec else None
                new_id = db.TblItemTopics.insert(item_type="P", item_id=pid, topic_id=topic.id, story_id=story_id)
                curr_tag_ids |= set([topic.id])
                added.append(item)
                topic_rec = db(db.TblTopics.id==topic.id).select().first()
                if 'P' not in topic_rec.usage:
                    usage = topic_rec.usage + 'P'
                    topic_rec.update_record(usage=usage, topic_kind=2) #simple topic
            elif topic.sign=="minus" and topic.id in curr_tag_ids:
                q = (db.TblItemTopics.item_type=="P") & (db.TblItemTopics.item_id==pid) & (db.TblItemTopics.topic_id==topic.id)
                curr_tag_ids -= set([topic.id])
                deleted.append(item)
                #should remove 'P' from usage if it was the last one...
                db(q).delete()
        curr_tags = [all_tags[tag_id] for tag_id in curr_tag_ids]
        keywords = "; ".join(curr_tags)
        rec = db(db.TblPhotos.id==pid).select().first()
        rec.update_record(KeyWords=keywords) #todo: remove this line soon
        rec1 = db(db.TblStories.id==rec.story_id).select().first()
        rec1.update_record(keywords=keywords)
        if photographer_id:
            rec.update_record(photographer_id=photographer_id)
            rec1 = db(db.TblPhotographers.id==photographer_id).select().first()
            kind = rec1.kind or ''
            if not 'P' in kind:
                kind += 'P'
                rec1.update_record(kind=kind)
        if dates_info:
            update_record_dates(rec, dates_info)
    ws_messaging.send_message('PHOTO-TAGS-CHANGED', added=added, deleted=deleted)
    return dict()

@serve_json
def save_video(vars):
    #https://photos.app.goo.gl/TndZ4fgyih57pmzS6 - shared google photos
    user_id = vars.user_id
    params = vars.params
    date_info = dict(video_date=(params.video_date_datestr, params.video_date_datespan))
    if not params.id: #creation, not modification
        pats = dict(
            youtube=r'https://(?:www.youtube.com/watch\?v=|youtu\.be/)(?P<code>[^&]+)',
            vimeo=r'https://vimeo.com/(?P<code>\d+)'
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
        q = (db.TblVideos.src==src) & (db.TblVideos.video_type==typ) & (db.TblVideos.deleted!=True)
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
        if params.video_date_datestr:
            rec = db(db.TblVideos.id==vid).select().first()
            date_data = dict(
                video_date_datestr=params.video_date_datestr,
                video_date_datespan=params.video_date_span
            )
            date_data_in = fix_record_dates_in(rec, date_data)
            rec.update_record(**date_data_in)
            data.update(video_date_datestr=params.video_date_datestr, video_date_datespan=params.video_date_datespan)
        else:
            data.update(video_date_datestr='1', video_date_datespan=0)
        ###update_record_dates(rec, date_info)
        ws_messaging.send_message(key='NEW-VIDEO', group='ALL', new_video_rec=data)
    else:
        old_rec = db(db.TblVideos.id==params.id).select().first()
        del params['src'] #
        #data = dict()
        #for fld in old_rec:
            #if fld in ('src', 'update_record', 'delete_record'):
                #continue
            #if old_rec[fld] != params[fld]:
                #data[fld] = params[fld]
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
    return dict()

@serve_json
def delete_video(vars):
    story_id = db(db.TblVideos.id==vars.video_id).select().first().story_id
    sm = stories_manager.Stories()
    sm.delete_story(story_id)
    n = db(db.TblVideos.id==vars.video_id).update(deleted=True)
    return dict()

@serve_json
def get_video_list(vars):
    selected_topics = vars.selected_topics or []
    if selected_topics:
        lst = get_video_list_with_topics(vars)
    else:
        q = make_videos_query(vars)
        lst = db(q).select()
    selected_video_list = vars.selected_video_list
    result = []
    if selected_video_list:
        lst1 = db(db.TblVideos.id.belongs(selected_video_list)).select()
        lst1 = [rec for rec in lst1]
        for rec in lst1:
            rec.selected = True
    else:
        lst1 = []
    lst1_ids = [rec.id for rec in lst1]
    lst = [rec for rec in lst if rec.id not in lst1_ids]
    lst = lst1 + lst
    ##lst = db(db.TblVideos.deleted != True).select()
    video_list = [rec for rec in lst]
    for rec in video_list:
        fix_record_dates_out(rec)
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
            photo_date = (vars.photos_date_str, vars.photos_date_span_size)
        )
    else:
        dates_info = None

    st = vars.selected_topics
    added = []
    deleted = []
    changes = dict()
    for vid in svl:
        curr_tag_ids = set(get_tag_ids(vid, "V"))
        for tpc in st:
            topic = tpc.option
            item = dict(item_id=vid, topic_id=topic.id)
            if topic.sign=="plus" and topic.id not in curr_tag_ids:
                vrec = db(db.TblVideos.id==vid).select().first()
                story_id = vrec.story_id if vrec else None
                if not story_id:
                    continue
                new_id = db.TblItemTopics.insert(item_type="V", item_id=vid, topic_id=topic.id, story_id=story_id) 
                curr_tag_ids |= set([topic.id])
                added.append(item)
                topic_rec = db(db.TblTopics.id==topic.id).select().first()
                if 'V' not in topic_rec.usage:
                    usage = topic_rec.usage + 'V'
                    topic_rec.update_record(usage=usage, topic_kind=2) #simple topic
            elif topic.sign=="minus" and topic.id in curr_tag_ids:
                q = (db.TblItemTopics.item_type=="V") & (db.TblItemTopics.item_id==vid) & (db.TblItemTopics.topic_id==topic.id)
                curr_tag_ids -= set([topic.id])
                deleted.append(item)
                db(q).delete()
        curr_tags = [all_tags[tag_id] for tag_id in curr_tag_ids]
        keywords = "; ".join(curr_tags)
        changes[vid] = dict(keywords=keywords, video_id=vid)
        rec = db(db.TblVideos.id==vid).select().first()
        rec.update_record(keywords=keywords) #todo: remove this line soon
        rec1 = db(db.TblStories.id==rec.story_id).select().first()
        rec1.update_record(keywords=keywords)
        if photographer_id:
            rec.update_record(photographer_id=photographer_id)
            rec1 = db(db.TblPhotographers.id==photographer_id).select().first()
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
    return dict()

@serve_json
def delete_selected_photos(vars):
    selected_photo_list = vars.selected_photo_list
    db(db.TblPhotos.id.belongs(selected_photo_list)).update(deleted=True)
    return dict()

@serve_json
def rotate_selected_photos(vars):
    selected_photo_list = vars.selected_photo_list
    for photo_id in selected_photo_list:
        rotate_photo(photo_id)
    return dict()

@serve_json
def promote_videos(vars):
    selected_video_list = vars.params.selected_video_list
    q = (db.TblVideos.id.belongs(selected_video_list))
    today = datetime.date.today()
    db(q).update(touch_time=today)
    return dict()

@serve_json
def get_video_sample(vars):
    q = (db.TblVideos.deleted==False)
    q1 = q & (db.TblVideos.touch_time != NO_DATE)
    lst1 = db(q1).select(limitby=(0, 10), orderby=~db.TblVideos.touch_time)
    lst1 = [rec.src for rec in lst1]
    q2 = q & (db.TblVideos.touch_time == NO_DATE)
    lst2 = db(q2).select(limitby=(0, 200))
    lst2 = [rec.src for rec in lst2]
    if len(lst2) > 10:
        lst2 = random.sample(lst2, 10)
    lst = lst1 + lst2
    return dict(video_list=lst)

####---------------support functions--------------------------------------

def get_photo_list_with_topics(vars):
    first = True
    topic_groups = calc_grouped_selected_options(vars.selected_topics)
    for topic_group in topic_groups:
        q = make_photos_query(vars) #if we do not regenerate it the query becomes accumulated and necessarily fails
        q &= (db.TblItemTopics.item_id==db.TblPhotos.id) & (db.TblItemTopics.item_type.like('%P%'))
        ##topic_ids = [t.id for t in topic_group]
        sign = topic_group[0]
        topic_group = topic_group[1:]
        q1 = db.TblItemTopics.topic_id.belongs(topic_group)
        if sign == 'minus':
            q1 = ~q1
        q &= q1
        lst = db(q).select()
        lst = [rec.TblPhotos for rec in lst]
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

def make_photos_query(vars):
    q = (db.TblPhotos.width > 0) & (db.TblPhotos.deleted!=True)
    #if vars.relevant_only:
        #q &= (db.TblPhotos.usage > 0)
    first_year = vars.first_year
    last_year = vars.last_year
    if vars.base_year: #time range may be defined
        if first_year < vars.base_year + 4:
            first_year = 0
        if last_year and last_year > vars.base_year + vars.num_years  - 5:
            last_year = 0
    else:
        first_year = 0
        last_year = 0
    photographer_list = [p.option.id for p in vars.selected_photographers] if vars.selected_photographers else []
    if len(photographer_list) > 0:
        q &= db.TblPhotos.photographer_id.belongs(photographer_list)
    if first_year:
        from_date = datetime.date(year=first_year, month=1, day=1)
        q &= (db.TblPhotos.photo_date >= from_date)
    if last_year:
        to_date = datetime.date(year=last_year, month=1, day=1)
        q &= (db.TblPhotos.photo_date < to_date)
    if vars.selected_days_since_upload:
        days = vars.selected_days_since_upload.value
        if days:
            upload_date = datetime.datetime.today() - datetime.timedelta(days=days)
            q &= (db.TblPhotos.upload_date >= upload_date)
    opt = vars.selected_uploader
    if opt == 'mine':
        q &= (db.TblPhotos.uploader==vars.user_id)
    elif opt == 'users':
        q &= (db.TblPhotos.uploader!=None)
    opt = vars.selected_dates_option
    if opt == 'selected_dates_option':
        pass
    elif opt == 'dated':
        q &= (db.TblPhotos.photo_date != NO_DATE)
    elif opt == 'undated':
        q &= (db.TblPhotos.photo_date == NO_DATE)
    if vars.selected_member_id:
        member_id = vars.selected_member_id
        q1 = (db.TblMemberPhotos.Member_id==member_id) & \
            (db.TblPhotos.id==db.TblMemberPhotos.Photo_id)
        q &= q1
    return q

def get_video_list_with_topics(vars):
    first = True
    topic_groups = calc_grouped_selected_options(vars.selected_topics)
    for topic_group in topic_groups:
        q = make_videos_query(vars) #if we do not regenerate it the query becomes accumulated and necessarily fails
        q &= (db.TblItemTopics.item_id==db.TblVideos.id) & (db.TblItemTopics.item_type.like('%V%'))
        ##topic_ids = [t.id for t in topic_group]
        sign = topic_group[0]
        topic_group = topic_group[1:]
        q1 = db.TblItemTopics.topic_id.belongs(topic_group)
        if sign == 'minus':
            q1 = ~q1
        q &= q1
        lst = db(q).select()
        lst = [rec.TblVideos for rec in lst]
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

def make_videos_query(vars):
    q = (db.TblVideos.deleted!=True)
    photographer_list = [p.option.id for p in vars.selected_photographers] if vars.selected_photographers else []
    if len(photographer_list) > 0:
        q &= db.TblVideos.photographer_id.belongs(photographer_list)
    if vars.selected_days_since_upload:
        days = vars.selected_days_since_upload.value
        if days:
            upload_date = datetime.datetime.today() - datetime.timedelta(days=days)
            q &= (db.TblVideos.upload_date >= upload_date)
    opt = vars.selected_uploader
    if opt == 'mine':
        q &= (db.TblVideos.uploader==vars.user_id)
    elif opt == 'users':
        q &= (db.TblVideos.uploader!=None)
    opt = vars.selected_dates_option
    if opt == 'selected_dates_option':
        pass
    elif opt == 'dated':
        q &= (db.TblVideos.video_date != NO_DATE)
    elif opt == 'undated':
        q &= (db.TblVideos.video_date == NO_DATE)
    return q

