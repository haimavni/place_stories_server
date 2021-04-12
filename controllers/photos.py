from photos_support import photos_folder, local_photos_folder, images_folder, local_images_folder, \
     save_uploaded_photo, rotate_photo, save_member_face, save_article_face, create_zip_file, get_photo_pairs, find_similar_photos, \
     timestamped_photo_path, crop_a_photo
import ws_messaging
import stories_manager
from date_utils import date_of_date_str, parse_date, get_all_dates, update_record_dates, fix_record_dates_in, fix_record_dates_out
from members_support import *
import random
import datetime
import os
import re
from gluon.storage import Storage
from gluon.utils import web2py_uuid

@serve_json
def upload_photo(vars):
    user_id = vars.user_id or auth.current_user()
    comment("start handling uploaded files")
    user_id = int(vars.user_id) if vars.user_id else auth.current_user()
    fil = vars.file
    #blob = to_bytes(fil.BINvalue)
    result = save_uploaded_photo(fil.name, fil.BINvalue, user_id)
    return dict(upload_result=result)

@serve_json
def get_photo_detail(vars):
    photo_id = int(vars.photo_id)
    if vars.what == 'story': #This photo is identified by the associated story
        rec = db((db.TblPhotos.story_id == photo_id) & (db.TblPhotos.deleted != True)).select().first()
    else:
        rec = db((db.TblPhotos.id == photo_id) & (db.TblPhotos.deleted != True)).select().first()
    sm = stories_manager.Stories()
    if not rec:
        return dict(photo_name='???')
    story=sm.get_story(rec.story_id)
    if not story:
        story = sm.get_empty_story(used_for=STORY4PHOTO)
    all_dates = get_all_dates(rec)
    photographer = db(db.TblPhotographers.id==rec.photographer_id).select().first()
    photographer_name = photographer.name if photographer else ''
    photographer_id = photographer.id if photographer else None
    photo_topics = get_photo_topics(rec.story_id)
    photo_pairs = get_photo_pairs([rec.id])
    if photo_pairs:
        back = photo_pairs[rec.id]
    else:
        back = None
    return dict(photo_src=timestamped_photo_path(rec, webp_supported=vars.webpSupported),
                photo_name=rec.Name,
                original_file_name=rec.original_file_name,
                embedded_photo_date=rec.embedded_photo_date,
                photo_topics=photo_topics,
                height=rec.height,
                width=rec.width,
                back=back,
                photo_story=story,
                photo_date_str = all_dates.photo_date.date,
                photo_date_datespan = all_dates.photo_date.span,
                photographer_name=photographer_name,
                photographer_id=photographer_id,
                photo_id=rec.id,
                latitude=rec.latitude,
                longitude=rec.longitude,
                zoom=rec.zoom,
                chatroom_id=story.chatroom_id)

@serve_json
def update_photo_caption(vars):
    photo_id = int(vars.photo_id)
    caption = vars.caption
    photo_rec = db((db.TblPhotos.id==photo_id) & (db.TblPhotos.deleted != True)).select().first()
    photo_rec.update(Name=caption, Recognized=True)
    sm = stories_manager.Stories()
    sm.update_story_name(photo_rec.story_id, caption)
    return dict(bla='bla')

@serve_json
def update_photo_date(vars):
    photo_date_str = vars.photo_date_str
    photo_dates_info = dict(
        photo_date = (vars.photo_date_str, int(vars.photo_date_datespan))
    )
    rec = db((db.TblPhotos.id==int(vars.photo_id)) & (db.TblPhotos.deleted != True)).select().first()
    update_record_dates(rec, photo_dates_info)
    #todo: save in db
    return dict()

@serve_json
def update_photo_location(vars):
    longitude = float(vars.longitude) if vars.longitude else None
    latitude = float(vars.latitude) if vars.latitude else None
    zoom = int(vars.zoom)
    if longitude:
        db(db.TblPhotos.id==int(vars.photo_id)).update(longitude=longitude, latitude=latitude, zoom=zoom)
    else:
        db(db.TblPhotos.id == int(vars.photo_id)).update(zoom=zoom)
    return dict()

@serve_json
def get_photo_info(vars):
    '''
    get photo info
    '''
    photo_id = int(vars.photo_id)
    rec = db(db.TblPhotos.id == photo_id).select().first()
    all_dates = get_all_dates(rec)
    if rec.photographer_id:
        photographer_rec = db(db.TblPhotographers.id == rec.photographer_id).select().first()
    else:
        photographer_rec = Storage()
    result = dict(
        name=rec.Name,
        description=rec.Description,
        photographer=photographer_rec.name,
        photo_date_str=all_dates.photo_date.date,
        photo_date_datespan=all_dates.photo_date.span,
        photo_date_dateunit=all_dates.photo_date.unit
    )
    return result

@serve_json
def save_photo_info(vars):
    '''
    save photo info
    '''
    pinf = vars.photo_info
    unit, date = parse_date(pinf.photo_date_str)
    photo_rec = db((db.TblPhotos.id == vars.photo_id) & (db.TblPhotos.deleted != True)).select().first()
    if pinf.name != photo_rec.Name:
        smgr = stories_manager.Stories(vars.user_id)
        smgr.update_story_name(photo_rec.story_id, pinf.name)
    photo_date_str = pinf.photo_date_str
    del pinf.photo_date_str
    pinf.photo_date = date
    pinf.photo_date_dateunit = unit
    del pinf.photographer
    pinf.Name = pinf.name
    del pinf.name
    pinf.Recognized = True
    photo_rec.update_record(**pinf)
    if photo_date_str:
        dates_info = dict(
            photo_date=(photo_date_str, pinf.photo_date_datespan)
        )
        update_record_dates(photo_rec, dates_info)
    return dict()

@serve_json
def get_faces(vars):
    '''
    get all faces on photo
    '''
    photo_id = vars.photo_id
    lst = db(db.TblMemberPhotos.Photo_id == photo_id).select()
    faces = []
    candidates = []
    for rec in lst:
        if rec.r == None: #found old record which has a member but no location
            if not rec.Member_id:
                db(db.TblMemberPhotos.id == rec.id).delete()
                continue
            name = member_display_name(member_id=rec.Member_id)
            candidate = dict(member_id=rec.Member_id, name=name)
            candidates.append(candidate)
        else:
            face = Storage(x=rec.x, y=rec.y, r=rec.r or 20, photo_id=rec.Photo_id)
            if rec.Member_id:
                face.member_id = rec.Member_id
                face.name = member_display_name(member_id=rec.Member_id)
            faces.append(face)
    face_ids = set([face.member_id for face in faces])
    candidates = [c for c in candidates if not c['member_id'] in face_ids]
    return dict(faces=faces, candidates=candidates)

@serve_json
def get_articles(vars):
    '''
    get all articles on photo
    '''
    photo_id = vars.photo_id
    q = (db.TblArticlePhotos.photo_id == photo_id) & (db.TblArticlePhotos.article_id == db.TblArticles.id)
    lst = db(q).select()
    articles = []
    for rec1 in lst:
        rec = rec1.TblArticlePhotos
        article = Storage(x=rec.x, y=rec.y, r=rec.r or 20, photo_id=rec.photo_id)
        if rec.article_id:
            article.article_id = rec.article_id
            article.name = rec1.TblArticles.name
        articles.append(article)
    article_ids = set([article.article_id for articls in articles])
    return dict(articles=articles)

@serve_json
def save_face(vars):
    return save_member_face(vars)

@serve_json
def save_article(vars):
    return save_article_face(vars)

@serve_json
def detach_photo_from_member(vars):
    member_id = int(vars.member_id)
    photo_id = int(vars.photo_id)
    q = (db.TblMemberPhotos.Photo_id == photo_id) & \
        (db.TblMemberPhotos.Member_id == member_id)
    good = db(q).delete() == 1
    ws_messaging.send_message(key='MEMBER_PHOTO_LIST_CHANGED', group='ALL', member_id=member_id, photo_id=photo_id)
    return dict(photo_detached=good)

@serve_json
def detach_photo_from_article(vars):
    article_id = vars.article_id
    photo_id = vars.photo_id
    q = (db.TblArticlePhotos.photo_id == photo_id) & \
        (db.TblArticlePhotos.article_id == article_id)
    good = db(q).delete() == 1
    n = db(db.TblArticlePhotos.article_id == article_id).count()
    if n == 0:
        db(db.TblArticles.id==article_id).update(deleted=True)
        ws_messaging.send_message(key='ARTICLE_DELETED', group='ALL', article_id=article_id)
    else:
        ws_messaging.send_message(key='ARTICLE_PHOTO_LIST_CHANGED', group='ALL', article_id=article_id, photo_id=photo_id)
    return dict(photo_detached=good)

def remove_duplicate_photo_members(): #todo: remove after all sites are fixed
    lst = db(db.TblMemberPhotos).select(orderby=db.TblMemberPhotos.Member_id | \
                                        db.TblMemberPhotos.Photo_id | \
                                                ~db.TblMemberPhotos.id)
    prev_rec = Storage()
    nd = 0
    for rec in lst:
        if rec.Member_id != prev_rec.Member_id or rec.Photo_id != prev_rec.Photo_id:
            prev_rec = rec
            continue
        nd += db(db.TblMemberPhotos.id == rec.id).delete()
    return '{} duplicate member/photo links were removed'.format(nd)

@serve_json
def get_photo_list(vars):
    mprl = vars.max_photos_per_line or 8
    MAX_PHOTOS_COUNT = 100 + (mprl - 8) * 100
    selected_order_option = vars.selected_order_option or ""
    last_photo_id = None
    last_photo_date = None
    q = make_photos_query(vars)
    total_photos = db(q).count()
    if selected_order_option == 'upload-time-order':
        if vars.count_limit:
            n = int(vars.count_limit)
        else:
            n = 200
        MAX_PHOTOS_COUNT = n
        last_photo_id = vars.last_photo_id
        if last_photo_id:
            q &= (db.TblPhotos.id < last_photo_id)
            total_photos = db(q).count()
        lst = db(q).select(orderby=~db.TblPhotos.id, limitby=(0, n))
        lst = list(lst)
        if lst:
            last_photo_id = lst[-1].TblPhotos.id
    elif selected_order_option.startswith('chronological-order'):
        if vars.count_limit:
            n = int(vars.count_limit)
        else:
            n = 200
        MAX_PHOTOS_COUNT = n
        last_photo_date = vars.last_photo_date
        last_photo_id = vars.last_photo_id
        if last_photo_date:
            if selected_order_option.endswith('reverse'):
                # since dates may be repeated, we need to sort by id too
                q &= (db.TblPhotos.photo_date < last_photo_date) | (db.TblPhotos.photo_date == last_photo_date) & (db.TblPhotos.id < last_photo_id)
            else:
                q &= (db.TblPhotos.photo_date > last_photo_date) | (db.TblPhotos.photo_date == last_photo_date) & (db.TblPhotos.id > last_photo_id)
            total_photos = db(q).count()
        field1 = db.TblPhotos.photo_date
        field2 = db.TblPhotos.id
        if selected_order_option.endswith('reverse'):
            field1 = ~field1
            field2 = ~field2
        lst = db(q).select(orderby=field1 | field2, limitby=(0, n))
        lst = list(lst)
    else:
        n = db(q).count()
        if n > MAX_PHOTOS_COUNT:
            frac = max(MAX_PHOTOS_COUNT * 100 / n, 1)
            frac = round(frac)
            sample = random.sample(list(range(1, 101)), frac)
            ##q &= (db.TblPhotos.random_photo_key <= frac)
            q &= (db.TblPhotos.random_photo_key.belongs(sample)) #we don't want to bore our users 
        lst = db(q).select() ###, db.TblPhotographers.id) ##, db.TblPhotographers.id)
        lst = list(lst)
        last_photo_id = None
    if len(lst) > MAX_PHOTOS_COUNT:
        lst1 = random.sample(lst, MAX_PHOTOS_COUNT)
        lst = lst1
    selected_photo_list = vars.selected_photo_list
    if selected_photo_list:
        lst1 = db(db.TblPhotos.id.belongs(selected_photo_list)).select()
        lst1 = [rec for rec in lst1]
        for rec in lst1:
            rec.selected = 'photo-selected'
    else:
        lst1 = []
    lst1_ids = [rec.id for rec in lst1]
    lst = [rec.TblPhotos for rec in lst if rec.TblPhotos.id not in lst1_ids]
    lst = lst1 + lst
    photo_ids = [rec.id for rec in lst]
    photo_pairs = get_photo_pairs(photo_ids)
    result = process_photo_list(lst, photo_pairs, webpSupported=vars.webpSupported)
    if selected_order_option == 'upload-time-order' and lst:
        if lst:
            last_photo_id = lst[-1].id
            q1 = q & (db.TblPhotos.id < last_photo_id)
            if db(q1).count() == 0:
                last_photo_id = 'END'
        else:
            last_photo_id = 'END'
    elif selected_order_option.startswith('chronological') and lst:
        if lst:
            last_photo_date = lst[-1].photo_date
            last_photo_id = lst[-1].id
            if selected_order_option.endswith('reverse'):
                q1 = (db.TblPhotos.photo_date < last_photo_date) | (db.TblPhotos.photo_date == last_photo_date) & (db.TblPhotos.id < last_photo_id)
            else:
                q1 = (db.TblPhotos.photo_date > last_photo_date) | (db.TblPhotos.photo_date == last_photo_date) & (db.TblPhotos.id > last_photo_id)
            if db(q & q1).count() == 0:
                last_photo_date = 'END'
        else:
            last_photo_date = 'END'
    else:
        #could keep here date + id for chronological order
        last_photo_id = None
    return dict(photo_list=result, last_photo_id=last_photo_id, last_photo_date=last_photo_date, total_photos=total_photos)

@serve_json
def get_theme_data(vars):
    path = images_folder()
    local_path = local_images_folder()
    files = dict(
        header_background='header-background.png',
        top_background='top-background.png',
        footer_background='footer-background.png',
        app_logo='app-logo.png',
        content_background='bgs/body-bg.jpg'
    )
    result = dict()
    for k in files:
        result[k] = path + files[k] if os.path.exists(local_path + files[k]) else ''
        if not os.path.exists(local_path + files[k]):
            pass
            #comment("file {} is missing", k)
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
            photo_date=(photos_date_str, vars.photos_date_span_size)
        )
    else:
        dates_info = None

    st = vars.selected_topics
    added = []
    deleted = []
    new_topic_was_added = False
    for pid in spl:
        rec = db(db.TblPhotos.id == pid).select().first()
        story_id = rec.story_id if rec else None
        curr_tag_ids = set(get_tag_ids(story_id, "P")) if story_id else set([])
        for tpc in st:
            topic = tpc.option
            item = dict(story_id=story_id, topic_id=topic.id)
            if topic.sign == "plus" and topic.id not in curr_tag_ids:
                new_id = db.TblItemTopics.insert(
                    item_type="P",
                    topic_id=topic.id,
                    story_id=story_id)
                curr_tag_ids |= set([topic.id])
                added.append(item)
                topic_rec = db(db.TblTopics.id == topic.id).select().first()
                if topic_rec.topic_kind == 0: #never used
                    new_topic_was_added = True
                if 'P' not in topic_rec.usage:
                    usage = topic_rec.usage + 'P'
                    topic_rec.update_record(usage=usage, topic_kind=2) #simple topic
            elif topic.sign == "minus" and topic.id in curr_tag_ids:
                q = (db.TblItemTopics.item_type == "P") & \
                    (db.TblItemTopics.story_id == story_id) & \
                    (db.TblItemTopics.topic_id == topic.id)
                curr_tag_ids -= set([topic.id])
                deleted.append(item)
                #should remove 'P' from usage if it was the last one...
                db(q).delete()
        curr_tags = [all_tags[tag_id] for tag_id in curr_tag_ids]
        keywords = "; ".join(curr_tags)
        if story_id:
            db(db.TblStories.id == story_id).update(keywords=keywords, is_tagged=bool(keywords))
        if rec:
            rec.update_record(Recognized=True)
        if photographer_id:
            rec.update_record(photographer_id=photographer_id)
            rec1 = db(db.TblPhotographers.id == photographer_id).select().first()
            kind = rec1.kind or ''
            if not 'P' in kind:
                kind += 'P'
                rec1.update_record(kind=kind)
        if dates_info:
            update_record_dates(rec, dates_info)
    ws_messaging.send_message('PHOTO-TAGS-CHANGED', added=added, deleted=deleted)
    return dict(new_topic_was_added=new_topic_was_added)

@serve_json
def apply_topics_to_photo(vars):
    all_tags = calc_all_tags()
    photo_id = int(vars.photo_id)
    rec = db(db.TblPhotos.id == photo_id).select().first()
    story_id = rec.story_id if rec else None
    topics = vars.topics
    curr_tag_ids = set(get_tag_ids(story_id, "P"))
    new_tag_ids = set([t.id for t in topics])
    added = set([])
    deleted = set([])
    for tag_id in new_tag_ids:
        if tag_id not in curr_tag_ids:
            added |= set([tag_id])
            db.TblItemTopics.insert(
                item_type="P",
                topic_id=tag_id,
                story_id=story_id)
            topic_rec = db(db.TblTopics.id == tag_id).select().first()
            if 'P' not in topic_rec.usage:
                usage = topic_rec.usage + 'P'
                topic_rec.update_record(usage=usage, topic_kind=2) #simple topic
                
    for tag_id in curr_tag_ids:  
        if tag_id not in new_tag_ids:
            deleted |= set([tag_id])
            q = (db.TblItemTopics.item_type == "P") & \
                (db.TblItemTopics.story_id == story_id) & \
                (db.TblItemTopics.topic_id == tag_id)
            #should remove 'P' from usage if it was the last one...
            db(q).delete()
            
    curr_tag_ids |= added
    curr_tag_ids -= deleted
    curr_tags = [all_tags[tag_id] for tag_id in curr_tag_ids]
    curr_tags = sorted(curr_tags)
    keywords = "; ".join(curr_tags)
    is_tagged = len(curr_tags) > 0
    srec = db(db.TblStories.id==rec.story_id).select().first()
    srec.update_record(keywords=keywords, is_tagged=is_tagged)
    rec.update_record(Recognized=True)
    
@serve_json
def assign_photo_photographer(vars):
    photo_id = int(vars.photo_id)
    photographer_id = int(vars.photographer_id) if vars.photographer_id else None
    db(db.TblPhotos.id==photo_id).update(photographer_id=photographer_id)
    return dict()

@serve_json
def delete_selected_photos(vars):
    delete_photos(vars.selected_photo_list)
    return dict()

@serve_json
def rotate_selected_photos(vars):
    selected_photo_list = vars.selected_photo_list
    rotate_clockwise = vars.rotate_clockwise
    if isinstance(rotate_clockwise, str):
        rotate_clockwise = rotate_clockwise == 'true';
    if not isinstance(selected_photo_list, list):
        selected_photo_list  = [int(selected_photo_list)];
    for photo_id in selected_photo_list:
        rotate_photo(photo_id, rotate_clockwise)
    return dict()

@serve_json
def mark_as_recogized(vars):
    db(db.TblPhotos.id==int(vars.photo_id)).update(Recognized = True)

@serve_json
def download_files(vars):
    pl = vars.selected_photo_list
    lst = db(db.TblPhotos.id.belongs(pl)).select()
    folder = local_photos_folder()
    oversize_folder = local_photos_folder("oversize")
    uuid = web2py_uuid()
    zip_name = "photos-" + uuid.split('-')[0]
    photo_list = []
    for p in lst:
        if p.oversize:
            photo_list.append(Storage(path=oversize_folder + p.photo_path, name=p.Name))
        else:
            photo_list.append(Storage(path=folder + p.photo_path, name=p.Name))
    create_zip_file(local_photos_folder("downloads") + zip_name, photo_list)
    download_url = photos_folder("downloads") + zip_name + ".zip"
    return dict(download_url=download_url)

@serve_json
def pair_selected_photos(vars):
    front_id, back_id = vars.selected_photo_list
    pair_photos(front_id, back_id)
    return dict(front_id=front_id, back_id=back_id)

@serve_json
def flip_photo(vars):
    if vars.to_unpair:
        was_flipped = False
        n = db(db.TblPhotoPairs.front_id==vars.back_id).delete()
        if not n: #was flipped
            was_flipped = True
            db(db.TblPhotoPairs.front_id==vars.front_id).delete()
        id = vars.back_id if was_flipped else vars.front_id
        recf = db(db.TblPhotos.id==id).select().first()
        recf.update_record(is_back_side = False)
        return dict(to_unpair=True)
    flip_photo_pair(vars.front_id, vars.back_id)
    return dict()

@serve_json
def crop_photo(vars):
    faces = db(db.TblMemberPhotos.Photo_id==vars.photo_id).select()
    crop_left = int(vars.crop_left)
    crop_top = int(vars.crop_top)
    crop_width = int(vars.crop_width)
    crop_height = int(vars.crop_height)
    for face in faces:
        if face.x:
            face.update_record(x=face.x - crop_left, y=face.y - crop_top)
    rec = db(db.TblPhotos.id==vars.photo_id).select().first()
    path = local_photos_folder("orig") + rec.photo_path
    curr_dhash = crop_a_photo(path, path, crop_left, crop_top, crop_width, crop_height)
    last_mod_time = request.now
    rec.update_record(width=crop_width, height=crop_height, last_mod_time=last_mod_time, curr_dhash=curr_dhash)
    return dict(photo_src=timestamped_photo_path(rec, webp_supported=vars.webpSupported))

@serve_json
def clear_photo_group(vars):
    pass

@serve_json
def find_duplicates(vars):
    lst, candidates = find_similar_photos(vars.selected_photos)
    photo_list = process_photo_list(lst)
    for prec in photo_list:
        prec['status'] = 'similar'
    return dict(photo_list=photo_list, got_duplicates=len(lst) > 0, candidates=list(candidates))

@serve_json
def get_uploaded_info(vars):
    uploaded_set = set(vars.uploaded)
    similars, candidates = find_similar_photos(vars.uploaded)
    duplicates  = vars.duplicates
    similar_set = set([p.id for p in similars])
    candidates = candidates & similar_set
    regulars = []
    for pid in vars.uploaded:
        if pid not in similar_set:
            regulars.append(pid)
    similar_photos = process_photo_list(similars)
    for prec in similar_photos:
        prec['status'] = 'similar'
    duplicates = db(db.TblPhotos.id.belongs(duplicates)).select()
    duplicate_photos = process_photo_list(duplicates)
    for prec in duplicate_photos:
        prec['status'] = 'duplicate'
    regulars = db(db.TblPhotos.id.belongs(regulars)).select()
    regular_photos = process_photo_list(regulars)
    for prec in regular_photos:
        prec['status'] = 'regular'
    photo_list = duplicate_photos + similar_photos + regular_photos
    return dict(photo_list=photo_list, candidates=list(candidates), got_duplicates=len(similars)>0)

@serve_json
def replace_duplicate_photos(vars):
    similars, candidates = find_similar_photos(vars.photos_to_keep)
    photos_to_keep_set = set(vars.photos_to_keep) & candidates #we do not allow automatic change to the old photo
    dup_grp = 0
    group = []
    photo_patches = []
    for prec in similars:
        if prec.dup_group != dup_grp:
            patch = handle_dup_group(group, photos_to_keep_set)
            if patch:
                photo_patches.append(patch)
            dup_grp = prec.dup_group
            group = [prec]
        else:
            group.append(prec)
    patch = handle_dup_group(group, photos_to_keep_set)
    if patch:
        photo_patches.append(patch)
    delete_photos(vars.photos_to_keep) #the image data was copied to the old photo which has more extra info
    return dict(photo_patches=photo_patches)

####---------------support functions--------------------------------------

def handle_dup_group(group, photos_to_keep_set):
    if not group:
        return None
    group = group[:2] #there should be no triplets but just in case...
    new_photo, old_photo = group
    if new_photo.id not in photos_to_keep_set:
        group = [old_photo, new_photo]
    data = replace_photo(group)
    #db(db.TblPhotos.id==new_photo.id).update(deleted=True) #todo: maybe just delete it...
    return dict(data=data, photo_to_patch=old_photo.id, photo_to_delete=new_photo.id)

def replace_photo(pgroup):
    '''
    we copy the image info from the newer, probably just uploaded, photo to the old photo record.
    We keep the old photo id to keep all references valid
    '''
    new_photo, old_photo = pgroup
    data = dict(
        photo_path=new_photo.photo_path,
        original_file_name=new_photo.original_file_name,
        width=new_photo.width,
        height=new_photo.height,
        uploader=new_photo.uploader,
        upload_date=new_photo.upload_date,
        last_mod_time=request.now,
        oversize=new_photo.oversize,
        crc=new_photo.crc,
        dhash=new_photo.dhash,
    )
    db(db.TblPhotos.id==old_photo.id).update(**data)
    db(db.TblPhotos.id==new_photo.id).update( #make the change undoable
        deleted=True,
        photo_path=old_photo.photo_path,
        original_file_name=old_photo.original_file_name,
        width=old_photo.width,
        height=old_photo.height,
        uploader=old_photo.uploader,
        upload_date=old_photo.upload_date,
        last_mod_time=request.now,
        oversize=old_photo.oversize,
        crc=old_photo.crc,
    dhash=old_photo.dhash,
    )
    ###data['status'] = 'regular'
    if old_photo.width != new_photo.width:
        ow, nw = old_photo.width, new_photo.width
        for member_photo_rec in db(db.TblMemberPhotos.Photo_id==old_photo.id).select():
            if not member_photo_rec.x:
                continue
            x = int(round(member_photo_rec.x * nw / ow))
            y = int(round(member_photo_rec.y * nw / ow))
            r = int(round(member_photo_rec.r * nw / ow))
            member_photo_rec.update_record(x=x, y=y, r=r)
    return data

def make_photos_query(vars):
    q = init_query(db.TblPhotos, editing=vars.editing, is_deleted=vars.deleted, user_id=vars.user_id)
    q &= (db.TblPhotos.width > 0) & \
        (db.TblPhotos.is_back_side != True)
    if vars.photo_ids:
        q &= (db.TblPhotos.id.belongs(vars.photo_ids))
    first_year = vars.first_year
    last_year = vars.last_year
    if vars.base_year: #time range may be defined
        if first_year < vars.base_year + 4:
            first_year = 0
        if last_year and last_year > vars.base_year + vars.num_years - 5:
            last_year = 0
    else:
        first_year = 0
        last_year = 0
    photographer_list = [p.option.id for p in vars.selected_photographers] \
        if vars.selected_photographers else []
    if len(photographer_list) > 0:
        q &= db.TblPhotos.photographer_id.belongs(photographer_list)
    if first_year:
        from_date = datetime.date(year=first_year, month=1, day=1)
        q &= (db.TblPhotos.photo_date_dateend >= from_date)
    if last_year:
        to_date = datetime.date(year=last_year, month=1, day=1)
        q &= (db.TblPhotos.photo_date < to_date)
    if vars.selected_days_since_upload:
        days = vars.selected_days_since_upload.value
        if days:
            upload_date = datetime.datetime.today() - datetime.timedelta(days=days)
            q &= (db.TblPhotos.upload_date >= upload_date)
    date_opt = vars.selected_uploader
    if date_opt == 'mine':
        user_id = auth.current_user() or vars.user_id
        q &= (db.TblPhotos.uploader == user_id)
    elif date_opt == 'users':
        q &= (db.TblPhotos.uploader != None)
    date_opt = vars.selected_dates_option
    selected_order_option = vars.selected_order_option or ""
    if date_opt == 'selected_dates_option':
        pass
    elif date_opt == 'dated' or selected_order_option.startswith('chronological-order'):
        q &= (db.TblPhotos.photo_date != NO_DATE)
    elif date_opt == 'undated':
        q &= (db.TblPhotos.photo_date == NO_DATE)
    member_ids = None
    if vars.selected_member_id:
        member_ids = [vars.selected_member_id]
    elif vars.selected_member_ids:
        member_ids = [int(mid) for mid in vars.selected_member_ids]
    if member_ids:
        q1 = with_members_query(member_ids)
        q &= q1
    if vars.selected_recognition == 'recognized':
        if date_opt != 'undated':
            q &= ((db.TblPhotos.Recognized == True) | (db.TblPhotos.Recognized == None))
    elif vars.selected_recognition == 'unrecognized':
        q &= (db.TblPhotos.Recognized == False)
    elif vars.selected_recognition == 'recognized-not-located':
        lst = unlocated_faces()
        q &= (db.TblPhotos.id.belongs(lst))
    if vars.show_untagged:
        q &= (db.TblPhotos.story_id==db.TblStories.id) & (db.TblStories.is_tagged==False)
    if vars.selected_topics:
        q1 = get_topics_query(vars.selected_topics)
        q &= q1
    return q 

def with_members_query(member_ids):
    result = None
    for mid in member_ids:
        q = (db.TblPhotos.id == db.TblMemberPhotos.Photo_id) & (db.TblMemberPhotos.Member_id == mid)
        lst = db(q).select(db.TblPhotos.id)
        lst = [r.id for r in lst]
        if result:
            result &= set(lst)
        else:
            result = set(lst)
    return (db.TblPhotos.id.belongs(result))

def unlocated_faces():
    q = (db.TblPhotos.id == db.TblMemberPhotos.Photo_id) & (db.TblMemberPhotos.x == None)
    lst = db(q).select(db.TblPhotos.id, db.TblMemberPhotos.id.count(), groupby=[db.TblPhotos.id], limitby=(0,5000))
    lst = [prec.TblPhotos.id for prec in lst]
    return lst
    
def pair_photos(front_id, back_id):
    rec = db((db.TblPhotoPairs.front_id == front_id) & (db.TblPhotos.deleted != True)).select().first()
    if rec:
        db(db.TblPhotos.id == rec.back_id).is_back_side = False
        db(db.TblPhotoPairs.id == rec.id).delete()
    db(db.TblPhotoPairs.back_id == back_id).delete()
    db.TblPhotoPairs.insert(front_id=front_id, back_id=back_id)
    db(db.TblPhotos.id == back_id).update(is_back_side=True)

def flip_photo_pair(front_id, back_id):
    #raise Exception("flip photo pair not ready")
    rec = db((db.TblPhotoPairs.front_id == front_id) & (db.TblPhotos.deleted != True)).select().first()
    if not rec: #already flipped
        return
    i = rec.TblPhotoPairs.id
    db(db.TblPhotoPairs.id == i).update(front_id=back_id, back_id=front_id)
    db(db.TblPhotos.id == front_id).update(is_back_side=True)
    db(db.TblPhotos.id == back_id).update(is_back_side=False)

def process_photo_list(lst, photo_pairs=dict(), webpSupported=False):
    for rec in lst:
        fix_record_dates_out(rec)
    result = []
    story_ids = [rec.story_id for rec in lst]
    lst1 = db(db.TblStories.id.belongs(story_ids)).select(db.TblStories.id, db.TblStories.keywords)
    kws = dict()
    for rec in lst1:
        kws[rec.id] = rec.keywords
    for rec in lst:
        tpp = timestamped_photo_path(rec, webp_supported=webpSupported)
        keywords=kws[rec.story_id]
        rec_title='{}: {}'.format(rec.Name, keywords)
        dic = Storage(
            description=rec.Description or "",
            name=rec.Name,
            original_file_name=rec.original_file_name,
            keywords=keywords,
            title=rec_title,
            photo_date_datestr=rec.photo_date_datestr,
            photo_date_span=rec.photo_date_datespan,
            photographer_id=rec.photographer_id,
            selected=rec.selected if 'selected' in rec else '',
            side='front',
            photo_id=rec.id,
            src=tpp,
            square_src=timestamped_photo_path(rec, what='squares', webp_supported=webpSupported),
            width=rec.width,
            height=rec.height,
            front=Storage(
                photo_id=rec.id,
                src=tpp,
                square_src=timestamped_photo_path(rec, what='squares', webp_supported=webpSupported),
                width=rec.width,
                height=rec.height,
            )
        )
        if rec.id in photo_pairs:
            dic.back = photo_pairs[rec.id]
            dic.flipped = False
            dic.flipable = 'flipable'
        result.append(dic)
    return result

def delete_photos(photo_list):
    a = db(db.TblPhotos.id.belongs(photo_list))
    a.update(deleted=True)
    story_ids = [rec.story_id for rec in a.select()]
    db(db.TblStories.id.belongs(story_ids)).update(deleted=True)

