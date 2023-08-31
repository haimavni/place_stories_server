import PIL
from PIL import Image, ImageFile
from PIL.ExifTags import TAGS, GPSTAGS
import dhash
from .injections import inject
import os
import array
import datetime
from distutils import dir_util
import zlib
from io import BytesIO
from .date_utils import datetime_from_str
from gluon.storage import Storage
import random
from sys import platform
if platform == 'linux':
    import pwd
from .stories_manager import Stories
from .folders import *
from .members_support import member_display_name, older_display_name, get_member_rec, init_query #init_query is used indirectly
import zipfile
from pybktree import BKTree, hamming_distance
import time
from . import ws_messaging
from misc_utils import multisort
from gluon._compat import to_bytes
import qrcode

MAX_WIDTH = 1200
MAX_HEIGHT = 800
DHASH_SIZE = 8

ImageFile.LOAD_TRUNCATED_IMAGES = True

def resized(width, height):
    x = 1.0 * MAX_WIDTH / width
    y = 1.0 * MAX_HEIGHT / height
    r = x if x < y else y
    return int(round(r * width)), int(round(r * height))

def crop_to_square(img, width, height, side_size):
    if width > height:
        x = (width - height) / 2
        x1 = width - x
        y = 0
        y1 = height
    else:
        y = (height - width) / 2
        y1 = height - y
        x = 0
        x1 = width
    area = (x, y, x1, y1)
    try:
        cropped_img = img.crop(area)
        resized_img = cropped_img.resize((side_size, side_size), Image.LANCZOS)
    except:
        return None
    return resized_img

def modification_date(filename):
    t = os.path.getmtime(filename)
    dt = datetime.datetime.fromtimestamp(t)
    return datetime.datetime(year=dt.year, month=dt.month, day=dt.day)

def save_uploaded_photo_collection(collection, user_id):
    duplicates = []
    failed = []
    photo_ids = []
    for file_name in collection:
        result = save_uploaded_photo(file_name, collection[file_name], user_id)
        if result.failed == 'failed':
            failed += [file_name]
        elif result.duplicate:
            duplicates += [result.duplicate]
        else:
            photo_ids.append(result.photo_id)
    return Storage(failed=failed,
                   duplicates=duplicates,
                   photo_ids=photo_ids)

def save_uploaded_photo(file_name, s, user_id, sub_folder=None):
    # NOT used in normal photos upload!
    auth, comment, log_exception, db, STORY4PHOTO, NO_DATE = inject('auth', 'comment', 'log_exception', 'db', 'STORY4PHOTO', 'NO_DATE')
    comment("enter save uploaded photo")
    user_id = user_id or auth.current_user()
    ###blob = bytearray(s)
    blob = to_bytes(s)
    crc = zlib.crc32(blob)
    prec = db((db.TblPhotos.crc==crc) & (db.TblPhotos.deleted != True)).select().first()
    if prec:
        if prec.has_geo_info:
            return Storage(duplicate=prec.id)
    original_file_name, ext = os.path.splitext(file_name)
    file_name = '{crc:x}{ext}'.format(crc=crc & 0xffffffff, ext=ext)
    today = datetime.date.today()
    month = str(today)[:-3]
    if not sub_folder:
        sub_folder = sub_folder or 'uploads/' + month + '/'
    path = local_photos_folder(RESIZED) + sub_folder
    dir_util.mkpath(path)
    latitude = None
    longitude = None
    zoom = None
    embedded_photo_date = None
    try:
        blob = array.array('B', [x for x in map(ord, s)]).tobytes()
        stream = BytesIO(blob)
        img = Image.open(stream)
        exif_data = get_exif_data(img)
        if 'GPSInfo' in exif_data:
            try:
                gps_info = exif_data['GPSInfo']
                lng = gps_info['GPSLongitude']
                lat = gps_info['GPSLatitude']
                longitude = degrees_to_float(lng)
                latitude = degrees_to_float(lat)
                if gps_info['GPSLatitudeRef'] == 'S':
                    latitude = -latitude
                if gps_info['GPSLongitudeRef'] == 'W':
                    longitude = -longitude
                zoom = 13
            except Exception as e:
                log_exception("getting photo geo data failed")
            if prec:
                has_geo_info = longitude != None
                prec.update_record(has_geo_info=has_geo_info, longitude=longitude, latitude=latitude, zoom=zoom)
                if prec.oversize:
                    fname = local_photos_folder(ORIG) + prec.photo_path
                    img.save(fname, quality=95)  ###, exif=img.info['exif'])
        if prec:
            return Storage(duplicate=prec.id)
        if 'DateTimeDigitized' in exif_data:
            s = exif_data['DateTimeDigitized']
            try:
                comment(f"embedded date is {s}")
                embedded_photo_date = datetime.datetime.strptime(s, '%Y:%m:%d %H:%M:%S')
            except Exception as e:
                log_exception('getting photo embedded date failed')
                
        width, height = img.size
        if width == 0:
            comment("!!!!!!!!!!!!!!!!!!!!!!! bad width/height !!!!!!!!!!!!!!!!!!")
        square_img = crop_to_square(img, width, height, 256)
        if square_img:
            path = local_photos_folder(SQUARES) + sub_folder
            dir_util.mkpath(path)
            square_img.save(path + file_name)
            fix_owner(path)
            fix_owner(path + file_name)
            got_square = True
        else:
            got_square = False
        oversize = False
        if height > MAX_HEIGHT or width > MAX_WIDTH:
            oversize = True
            path = local_photos_folder(ORIG) + sub_folder
            dir_util.mkpath(path)
            img.save(path + file_name, quality=95) ###, exif=img.info['exif'])
            fix_owner(path)
            fix_owner(path + file_name)
            width, height = resized(width, height)
            img = img.resize((width, height), Image.LANCZOS)
        elif height < MAX_HEIGHT and width < MAX_WIDTH:
            width, height = resized(width, height)
            img = img.resize((width, height), Image.LANCZOS)
        path = local_photos_folder(RESIZED) + sub_folder
        ###exif = img.info['exif'] if img.info and 'exif' in img.info e
        img.save(path + file_name, quality=100) ###, exif=img.info['exif'])
        fix_owner(path)
        fix_owner(path + file_name)
        dhash_value = dhash_photo(img=img)
    except Exception as e:
        log_exception("saving photo {} failed".format(original_file_name))
        return Storage(failed=1)
    sm = Stories()
    story_info = sm.get_empty_story(used_for=STORY4PHOTO, story_text="", name=original_file_name)
    result = sm.add_story(story_info)
    story_id = result.story_id

    if embedded_photo_date and not original_file_name.startswith("scanned"):
        photo_date = embedded_photo_date.date()
        photo_date_dateend = photo_date + datetime.timedelta(days=1)
        photo_date_dateunit = 'D'
        photo_date_datespan = 1
    else:
        photo_date = NO_DATE
        photo_date_dateend = NO_DATE
        photo_date_dateunit = 'Y'
        photo_date_datespan = 1
    has_geo_info = longitude != None
    photo_id = db.TblPhotos.insert(
        photo_path=sub_folder + file_name,
        original_file_name=original_file_name,
        name=original_file_name,
        embedded_photo_date=embedded_photo_date,
        uploader=user_id,
        upload_date=datetime.datetime.now(),
        photo_date=photo_date,
        photo_date_dateend=photo_date_dateend,
        photo_date_dateunit=photo_date_dateunit,
        photo_date_datespan=photo_date_datespan,
        width=width,
        height=height,
        latitude=latitude,
        longitude=longitude,
        has_geo_info=has_geo_info,
        zoom=13,
        crc=crc,
        dhash=dhash_value,
        oversize=oversize,
        photo_missing=False,
        deleted=False,
        story_id=story_id,
        random_photo_key=random.randint(1, 101)
    )
    db.commit()
    return Storage(photo_id=photo_id)

def get_image_info(image_path):
    img = Image.open(image_path)
    width, height = img.size
    faces = []
    return Storage(width=width, height=height, faces=faces)

def fit_size(rec):
    db, log_exception = inject('db', 'log_exception')
    fname = local_photos_folder(RESIZED) + rec.photo_path
    try:
        img = Image.open(fname)
        oversize_file_name = local_photos_folder(ORIG) + rec.photo_path
        oversize_path, f = os.path.split(oversize_file_name)
        dir_util.mkpath(oversize_path)
        img.save(oversize_file_name)
        width, height = resized(rec.width, rec.height)
        img = img.resize((width, height), Image.LANCZOS)
        img.save(fname)
        rec.update_record(width=width, height=height)
    except Exception as e:
        log_exception("resizing file {} failed.".format(rec.photo_path))
        rec.update_record(photo_missing=True)
        return False
    return True

def fit_all_sizes():
    db, request = inject('db', 'request')
    q = (db.TblPhotos.width > MAX_WIDTH) | (db.TblPhotos.height > MAX_HEIGHT)
    q &= (db.TblPhotos.photo_missing != True) & (db.TblPhotos.deleted!=True)
    chunk = 100
    num_failed = 0
    while True:
        n = db(q).count()
        if db(q).count() == 0:
            break
        lst = db(q).select(limitby=(0, chunk))
        for rec in lst:
            if not fit_size(rec):
                num_failed += 1
        db.commit()
    return dict(num_failed=num_failed)

def scan_all_unscanned_photos():
    db, request, comment = inject('db', 'request', 'comment')
    q = (db.TblPhotos.crc==None) & (db.TblPhotos.photo_missing == False) & (db.TblPhotos.deleted!=True)
    to_scan = db(q).count()
    comment(f"{to_scan} photos still unscanned")
    failed_crops = 0
    chunk = 100
    folder = local_photos_folder(RESIZED)
    while True:
        comment('started scanning chunk of photos')
        lst = db(q).select(limitby=(0, chunk))
        if not len(lst):
            comment('No unscanned photos were found!')
            return dict(message='No unscanned photos were found!', to_scan=to_scan)
        for rec in lst:
            if not rec.photo_path:
                continue
            fname = folder + rec.photo_path
            if not os.path.exists(fname):
                rec.update_record(photo_missing=True)
                continue
            inf = get_image_info(fname)
            width, height, faces = inf.width, inf.height, inf.faces
            with open(fname, 'r') as f:
                blob = f.read()
            crc = zlib.crc32(blob)
            rec.update_record(width=width, height=height, crc=crc)
            if not crop_square(fname, width, height, 256):
                failed_crops += 1
            for face in faces:
                x, y, w, h = face
                db.TblMemberPhotos.insert(photo_id=rec.id, x=x, y=y, w=w, h=h) # for older records,
                                                            # merge with record photo_id-member_id
        db.commit()
        missing = db((db.TblPhotos.photo_missing == True) & \
                     (db.TblPhotos.deleted != True)).count()
        done = db((db.TblPhotos.width > 0) & (db.TblPhotos.deleted != True)).count()
        total = db((db.TblPhotos) & (db.TblPhotos.deleted != True)).count()
    return dict(done=done, total=total, missing=missing, to_scan=to_scan, failed_crops=failed_crops)

def calc_missing_dhash_values(max_to_hash=20000):
    db, comment = inject('db', 'comment')
    q = (db.TblPhotos.dhash == None) & \
        (db.TblPhotos.photo_missing == False) & \
        (db.TblPhotos.deleted != True)
    to_scan = db(q).count()
    comment(f"{to_scan} photos still have no dhash value")
    chunk = 100
    folder = local_photos_folder(RESIZED)
    done = 0
    while True:
        comment('started dhashing chunk of photos')
        lst = db(q).select(limitby=(0, chunk))
        if not lst:
            comment('No more undhashed photos found!')
            break
        for rec in lst:
            if not rec.photo_path:
                continue
            fname = folder + rec.photo_path
            if not os.path.exists(fname):
                rec.update_record(photo_missing=True)
                continue
            dhash_value = dhash_photo(photo_path=fname)
            rec.update_record(dhash=dhash_value)
            done += 1
        db.commit()
        if done > max_to_hash:
            break
    to_scan = db(q).count()
    return  '{} photo records dhashed. {} need to be dhashed.'.format(done, to_scan)

def get_video_thumbnails(q):
    db = inject('db')
    lst = db(q).select()
    if not lst:
        return []
    if 'TblVideos' in lst[0]:
        lst = [rec.TblVideos for rec in lst]
    slides = []
    for rec in lst:
        dic = dict(
            video_id=rec.id,
            src=rec.thumbnail_url, 
            # src=thumbnail_url(rec.src),
            title=rec.name
        )
        slides.append(dic)
    return slides

def thumbnail_url(src):
    return f"https://i.ytimg.com/vi/{src}/mq2.jpg"

def get_slides_from_photo_list(q):
    db = inject('db')
    q &= (db.TblPhotos.width > 0)
    lst = db(q).select()
    if not lst:
        return []
    if 'TblPhotos' in lst[0]:
        lst = [rec.TblPhotos for rec in lst]
    lst1 = []
    visited = set([])
    for rec in lst:
        if rec.id in visited:
            continue
        visited |= set([rec.id])
        lst1.append(rec)
    lst = lst1

    photo_ids = [rec.id for rec in lst]
    photo_pairs = get_photo_pairs(photo_ids)
    slides = []
    for rec in lst:
        dic = dict(
            photo_id=rec.id,
            side='front',
            front=dict(
                photo_id=rec.id,
                src=timestamped_photo_path(rec),
                width=rec.width,
                height=rec.height,
                has_story_text=rec.has_story_text
                ),
            src=timestamped_photo_path(rec),
            width=rec.width,
            height=rec.height,
            has_story_text=rec.has_story_text,
            title=rec.description or rec.name)
        if rec.id in photo_pairs:
            dic['back'] = photo_pairs[rec.id]
            dic['flipped'] = False
            dic['flipable'] = 'flipable'
        slides.append(dic)
    return slides

def crop(input_path, output_path, face, size=100):
    img = Image.open(input_path)
    area = (face.x - face.r, face.y - face.r, face.x + face.r, face.y + face.r)
    cropped_img = img.crop(area)
    resized_img = cropped_img.resize((size, size), Image.LANCZOS)
    if input_path.lower().endswith(".png"):
        resized_img.save(output_path, format="png")
    else:
        resized_img.save(output_path)

def crop_a_photo(input_path, output_path, crop_left, crop_top, crop_width, crop_height):
    img = Image.open(input_path)
    area = (crop_left, crop_top, crop_left + crop_width, crop_top + crop_height)
    cropped_img = img.crop(area)
    #os.remove(input_path) #todo: for now keep the old file so changes in __test do not harm __www
    cropped_img.save(output_path)
    curr_dhash = dhash_photo(photo_path=output_path)
    return curr_dhash

def crop_square(img_src, width, height, side_size):
    if width > height:
        x = (width - height) / 2
        x1 = width - x
        y = 0
        y1 = height
    else:
        y = (height - width) / 2
        y1 = height - y
        x = 0
        x1 = width
    input_path = img_src
    path, fname = os.path.split(input_path)
    path = path.replace(RESIZED, SQUARES)
    dir_util.mkpath(path)
    output_path = path  + '/' +fname
    img = Image.open(input_path)
    area = (x, y, x1, y1)
    try:
        cropped_img = img.crop(area)
        resized_img = cropped_img.resize((side_size, side_size), Image.LANCZOS)
        resized_img.save(output_path)
    except:
        return False
    return True

def rotate_photo(photo_id, rotate_clockwise=False):
    db = inject('db')
    photo_rec = db((db.TblPhotos.id == photo_id) & (db.TblPhotos.deleted != True)).select().first()
    lst = [RESIZED, SQUARES, ORIG]
    for what in lst:
        path = local_photos_folder(what)
        file_name = path + photo_rec.photo_path
        if not os.path.exists(file_name):
            continue
        img = Image.open(file_name)
        angle = Image.ROTATE_270 if rotate_clockwise else Image.ROTATE_90
        img = img.transpose(angle)
        if what == RESIZED:
            img.save(file_name)
            with open(file_name, 'rb') as f:
                blob = f.read()
            crc = zlib.crc32(blob)
            pname, fname = os.path.split(photo_rec.photo_path)
            original_file_name, ext = os.path.splitext(fname)
            new_fname = '{crc:x}{ext}'.format(crc=crc & 0xffffffff, ext=ext)
            new_photo_path = pname + new_fname
            new_file_name = path + new_photo_path
            os.rename(file_name, new_file_name)
            curr_dhash = dhash_photo(photo_path=new_file_name)
            photo_rec.update_record(curr_dhash=curr_dhash)
        else:
            img.save(path + new_photo_path)
            ws_messaging.send_message(key='PHOTO_WAS_ROTATED', group='ALL', photo_id=photo_id)
    height, width = (photo_rec.width, photo_rec.height)
    photo_rec.update_record(width=width, height=height, photo_path=new_photo_path)

def resize_photo(photo_id, target_width=1200, target_height=800):
    db = inject('db')
    prec = db(db.TblPhotos.id==photo_id).select().first()
    what = ORIG if prec.oversize else RESIZED
    path = local_photos_folder(what)
    input_file_name = path + prec.photo_path
    if not os.path.exists(input_file_name):
        return
    img = Image.open(input_file_name)
    path = local_photos_folder(RESIZED)
    file_name = path + prec.photo_path
    image_width, image_height = img.size
    rw = 1.0 * target_width / image_width
    rh = 1.0 * target_height / image_height
    ratio1 = min(rw, rh)
    ratio2 = max(rw, rh)
    if ratio2 < 1.0 or ratio1 > 1.0:
        width = int(round(ratio1 * image_width))
        height = int(round(ratio1 * image_height))
        resized_img = img.resize((width, height), Image.LANCZOS)
        prec.update_record(width=width, height=height)
        resized_img.save(file_name)
        faces = db(db.TblMemberPhotos.photo_id == photo_id).select()
        for face in faces:
            if not face.x:
                return
            x = int(round(ratio1 * face.x))
            y = int(round(ratio1 * face.y))
            r = int(round(ratio1 * face.r))
            face.update_record(x=x, y=y, r=r)

def resize_photos(count, target_width=1200, target_height=800):
    db = inject('db')
    q = (db.TblPhotos.deleted != True) & (db.TblPhotos.width < target_width) & (db.TblPhotos.height < target_height)
    lst = db(q).select(db.TblPhotos.id, limitby=(0, count))
    lst = [prec.id for prec in lst]
    for pid in lst:
        resize_photo(pid, target_width, target_height)
    n = db(q).count()
    return dict(num_to_resize=n)

def add_photos_from_drive(sub_folder):
    folder = local_photos_folder(RESIZED)
    root_folder = folder + sub_folder
    for root, dirs, files in os.walk(root_folder, topdown=True):
        for file_name in files:
            path = root + '/' + file_name
            with open(path, 'r') as f:
                blob = f.read()
            result = save_uploaded_photo(file_name, blob, 1, sub_folder=sub_folder)
            if result.failed or result.duplicate:
                continue
            #delete the file. it has been saved using crc as name and was possibly resized
            os.remove(path)

def fix_owner(file_name):
    if platform != 'linux':
        return
    if os.getuid() > 0:
        return
    request = inject('request')
    host = request.env.http_host or ""
    if '8000' in host: #development
        return
    uid, gid = pwd.getpwnam('www-data')[2:4]
    os.chown(file_name, uid, gid)

def dhash_photo(photo_path=None, img=None):
    if not img:
        img = Image.open(photo_path)
    row_hash, col_hash = dhash.dhash_row_col(img)
    return dhash.format_hex(row_hash, col_hash)

def profile_photo_moved(face):
    db = inject('db')
    member_profile_photo_path = db(db.TblMembers.id==face.member_id).select().first().facephotourl
    if member_profile_photo_path:
        lst = member_profile_photo_path.split('-')
        photo_id = int(lst[2].split('.')[0])
    else:
        photo_id = face.photo_id
    return photo_id == face.photo_id

def article_profile_photo_moved(face):
    db = inject('db')
    article_profile_photo_path = db(db.TblArticles.id==face.article_id).select().first().facephotourl
    lst = article_profile_photo_path.split('-')
    photo_id = int(lst[2].split('.')[0])
    return photo_id == face.photo_id

def save_member_face(params):
    db, auth = inject('db', 'auth')
    face = params.face
    assert face.member_id > 0
    if params.make_profile_photo or profile_photo_moved(face):
        face_photo_url = save_profile_photo(face, is_article=False)
    else:
        face_photo_url = None
    if params.old_member_id and params.old_member_id > 0:
        q = (db.TblMemberPhotos.photo_id == face.photo_id) & \
            (db.TblMemberPhotos.member_id == params.old_member_id)
    else:
        q = (db.TblMemberPhotos.photo_id == face.photo_id) & \
            (db.TblMemberPhotos.member_id == face.member_id)
    who_identified = auth.current_user()
    data = dict(
        photo_id=face.photo_id,
        member_id=face.member_id,
        r=face.r,
        x=face.x,
        y=face.y,
        who_identified=who_identified
    )
    rec = db(q).select().first()
    if rec:
        rec.update_record(**data)
    else:
        db.TblMemberPhotos.insert(**data)
        if params.old_member_id and params.old_member_id > 0 and params.old_member_id != face.member_id:
            db(q).delete()
    member_name = member_display_name(member_id=face.member_id)
    db(db.TblPhotos.id==face.photo_id).update(recognized=True, handled=True)
    ws_messaging.send_message(key='MEMBER_PHOTO_LIST_CHANGED', group='ALL', article_id=face.article_id, photo_id=face.photo_id)
    if face_photo_url:
        face_photo_url = photos_folder(PROFILE_PHOTOS) + face_photo_url 
    return Storage(member_name=member_name, face_photo_url=face_photo_url)

def save_article_face(params):
    db, auth = inject('db', 'auth')
    face = params.face
    assert face.article_id > 0
    if params.make_profile_photo or article_profile_photo_moved(face):
        face_photo_url = save_profile_photo(face, is_article=True)
    else:
        face_photo_url = None
    if params.old_article_id:
        q = (db.TblArticlePhotos.photo_id == face.photo_id) & \
            (db.TblArticlePhotos.article_id == params.old_article_id)
    else:
        q = (db.TblArticlePhotos.photo_id == face.photo_id) & \
            (db.TblArticlePhotos.article_id == face.article_id)
    who_identified = auth.current_user()
    data = dict(
        photo_id=face.photo_id,
        article_id=face.article_id,
        r=face.r,
        x=face.x,
        y=face.y,
        who_identified=who_identified
    )
    rec = db(q).select().first()
    if rec:
        rec.update_record(**data)
    else:
        aid = db.TblArticlePhotos.insert(**data)
        if params.old_article_id and params.old_article_id != face.article_id:
            db(q).delete()
    rec = db(db.TblArticles.id==face.article_id).select().first()
    article_name = rec.name
    db(db.TblPhotos.id==face.photo_id).update(recognized=True, handled=True)
    ws_messaging.send_message(key='ARTICLE_PHOTO_LIST_CHANGED', group='ALL', article_id=face.article_id, photo_id=face.photo_id)
    if face_photo_url:
        face_photo_url = photos_folder(PROFILE_PHOTOS) + face_photo_url
    return Storage(article_name=article_name, face_photo_url=face_photo_url)

def save_profile_photo(face, is_article=False):
    db = inject('db')
    rec = get_photo_rec(face.photo_id)
    input_path = local_photos_folder(RESIZED) + rec.photo_path
    prefix = "AP" if is_article else "PP"
    iid = face.article_id if is_article else face.member_id
    facephotourl = f"{prefix}-{iid}-{face.photo_id}.jpg" #todo: just add ?filedate when used
    output_path = local_photos_folder(PROFILE_PHOTOS) + facephotourl
    crop(input_path, output_path, face)
    now = datetime.datetime.now()
    timestamp = int(round(now.timestamp()))
    facephotourl += f"?d={timestamp}"
    if is_article:
        db(db.TblArticles.id == face.article_id).update(facephotourl=facephotourl)
        ws_messaging.send_message('ARTICLE_PROFILE_CHANGED', group='ALL', 
            article_id=face.article_id, face_photo_url=photos_folder(PROFILE_PHOTOS) + facephotourl)
    else:
        db(db.TblMembers.id == face.member_id).update(facephotourl=facephotourl)
        ws_messaging.send_message('PHOTO_PROFILE_CHANGED', group='ALL', 
            member_id=face.member_id, face_photo_url=photos_folder(PROFILE_PHOTOS) + facephotourl)
    return facephotourl

def get_photo_rec(photo_id):
    db = inject('db')
    rec = db((db.TblPhotos.id == photo_id) & (db.TblPhotos.deleted != True)).select().first()
    return rec

def create_zip_file(zip_name, file_list):
    with zipfile.ZipFile(zip_name + '.zip', 'w') as myzip:
        for p in file_list:
            name, ext = os.path.splitext(p.path)
            myzip.write(p.path, arcname=p.name + ext)

def get_photo_pairs(photo_list):
    db = inject('db')
    q = (db.TblPhotoPairs.front_id.belongs(photo_list) & \
         (db.TblPhotos.id == db.TblPhotoPairs.back_id) & \
        (db.TblPhotos.deleted != True))
    lst = db(q).select(db.TblPhotoPairs.front_id, db.TblPhotoPairs.back_id,
                       db.TblPhotos.photo_path, db.TblPhotos.width, db.TblPhotos.height)
    result = dict()
    for rec in lst:
        result[rec.TblPhotoPairs.front_id] = dict(
            src=photos_folder(RESIZED) + rec.TblPhotos.photo_path,
            square_src=photos_folder(SQUARES) + rec.TblPhotos.photo_path,
            photo_id=rec.TblPhotoPairs.back_id,
            width=rec.TblPhotos.width,
            height=rec.TblPhotos.height
        )
    return result

def fix_missing_story_ids():
    db, STORY4PHOTO = inject('db', 'STORY4PHOTO')
    for prec in db(db.TblPhotos.deleted == None).select():
        prec.update(deleted=False)
    sm = Stories()
    lst = db((db.TblPhotos.story_id == None) & (db.TblPhotos.deleted != True)).select()
    for prec in lst:
        story_info = sm.get_empty_story(used_for=STORY4PHOTO, story_text="", name=prec.name)
        result = sm.add_story(story_info)
        story_id = result.story_id
        prec.update_record(story_id=story_id)
    return dict(story_less=len(lst))

def find_similar_photos(photo_list=None, time_budget=60):
    threshold = 15
    db, comment = inject('db', 'comment')
    tree = BKTree(hamming_distance)
    cnt = 0
    for photo_rec in db(db.TblPhotos.deleted != True).select(db.TblPhotos.dhash, db.TblPhotos.curr_dhash):
        if not photo_rec.dhash:
            continue
        tree.add(int(photo_rec.dhash, 16))
        if photo_rec.curr_dhash:
            tree.add(int(photo_rec.curr_dhash, 16))
        cnt += 1
    dup_list = []
    time0 = datetime.datetime.now()
    #if isinstance(photo_list, list) and len(photo_list) == 0: #If only preexisting photos were uploaded, do not search all similars
        #return []
    if photo_list == None:
        q = (db.TblPhotos.deleted != True) & (db.TblPhotos.dup_checked==None) & (db.TblPhotos.photo_missing==False)
    elif photo_list:
        q = db.TblPhotos.id.belongs(photo_list) & (db.TblPhotos.deleted != True)
    else:
        return ([], set([]))
    cnt = 0
    candidates = set([])
    dic = dict()
    visited = set()
    no_dhash = 0
    nv = 0
    for photo_rec in db(q).select(db.TblPhotos.id, db.TblPhotos.dhash, db.TblPhotos.curr_dhash, db.TblPhotos.dup_checked):
        if not photo_rec.dhash:
            no_dhash += 1
            continue
        if photo_rec.dhash in visited:
            nv += 1
            continue
        dif = datetime.datetime.now() - time0
        elapsed = int(dif.total_seconds())
        if elapsed > time_budget:
            break
        lst = tree.find(int(photo_rec.dhash, 16), threshold)
        if photo_rec.curr_dhash:
            lst += tree.find(int(photo_rec.curr_dhash, 16), threshold)
        if len(lst) > 1:
            comment(f".......................dups lst: {lst}")
            cnt += 1
            for itm in lst:
                visited.add(itm[1])
            dist = lst[1][0]
            lst = [itm for itm in lst if itm[0] <= dist]
            dhash_values = ['{:032x}'.format(itm[1]) for itm in lst]
            duplicate_photo_ids = db((db.TblPhotos.dhash.belongs(dhash_values)) & \
                                     (db.TblPhotos.deleted != True)).select(db.TblPhotos.id, orderby=db.TblPhotos.id)
            duplicate_photo_ids = [p.id for p in duplicate_photo_ids]
            curr_duplicate_photo_ids = db((db.TblPhotos.curr_dhash != None) & \
                                          (db.TblPhotos.curr_dhash.belongs(dhash_values)) & \
                                          (db.TblPhotos.deleted != True)).select(db.TblPhotos.id, orderby=db.TblPhotos.id)
            curr_duplicate_photo_ids = [p.id for p in curr_duplicate_photo_ids]
            duplicate_photo_ids += curr_duplicate_photo_ids
            if duplicate_photo_ids[0] in dic:
                continue #this group already visited
            for pid in duplicate_photo_ids:
                dic[pid] = cnt 
            dup_list.append(duplicate_photo_ids)
            cand = max(duplicate_photo_ids)
            candidates |= set([cand]) #Normally newer photos are better
        else:
            photo_rec.update_record(dup_checked = True)
    all_dup_ids = []
    for dup_ids in dup_list:
        all_dup_ids += dup_ids
    result = db((db.TblPhotos.id.belongs(all_dup_ids)) & (db.TblPhotos.deleted != True)).select()
    for photo_rec in result:
        photo_rec.dup_group = dic[photo_rec.id]
    result = [Storage(rec) for rec in result]
    ##result = sorted(result, cmp=lambda prec1, prec2: +1 if prec1.dup_group > prec2.dup_group else -1 if prec1.dup_group < prec2.dup_group else +1 if prec1.id < prec2.id else -1)
    result = multisort(result, (('dup_group', False), ('id', True)))
    return result, candidates

def timestamped_photo_path(photo_rec, webp_supported=True, what=RESIZED):
    #todo: if file for type of webp support is missing, create it?
    folder = photos_folder(what)
    result = folder + (photo_rec.photo_path_webp if webp_supported and photo_rec.webp_photo_path else photo_rec.photo_path)
    if photo_rec.last_mod_time:
        utime = time.mktime(photo_rec.last_mod_time.timetuple())
        result += '?' + str(utime)
    return result

def find_missing_files(init=False):
    db = inject('db')
    q = (db.TblPhotos.deleted != True) & (db.TblPhotos.photo_missing == None)
    n = db(q).count()
    if init:
        db(db.TblPhotos.deleted != True).update(photo_missing = None)
    chunk = 100
    recoverable = 0
    while True:
        lst = db(q).select(limitby=(0,chunk))
        if len(lst) == 0:
            break
        for rec in lst:
            fname = local_photos_folder(RESIZED) + rec.photo_path
            lost = not os.path.exists(fname)
            if lost:
                fname = local_photos_folder(ORIG) + rec.photo_path
                if os.path.exists(fname):
                    recoverable += 1
            rec.update_record(photo_missing=lost)
        db.commit()
    missing = db((db.TblPhotos.deleted!=True)&(db.TblPhotos.photo_missing==True)).count()
    return dict(missing=missing, recoverable=recoverable)

def create_watermark(image_path, final_image_path, watermark):
    #https://pybit.es/pillow-intro.html
    main = Image.open(image_path)
    mark = Image.open(watermark)

    mask = mark.convert('L').point(lambda x: min(x, 25))
    mark.putalpha(mask)

    mark_width, mark_height = mark.size
    main_width, main_height = main.size
    aspect_ratio = mark_width / mark_height
    new_mark_width = main_width * 0.25
    mark.thumbnail((new_mark_width, new_mark_width / aspect_ratio), Image.ANTIALIAS)

    tmp_img = Image.new('RGB', main.size)

    for i in range(0, tmp_img.size[0], mark.size[0]):
        for j in range(0, tmp_img.size[1], mark.size[1]):
            main.paste(mark, (i, j), mark)
            main.thumbnail((8000, 8000), Image.ANTIALIAS)
            main.save(final_image_path, quality=100)

def get_exif_data(image):
    """Returns a dictionary from the exif data of an PIL Image item. Also converts the GPS Tags"""
    exif_data = {}
    info = None
    try:
        info = image._getexif()
    except Exception as e:
        pass #png, for example
    if info:
        for tag, value in list(info.items()):
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_data = {}
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_data[sub_decoded] = value[t]

                exif_data[decoded] = gps_data
            else:
                exif_data[decoded] = value
    return exif_data   

def jpg_to_webp(file_name):
    img = Image.open(file_name).convert("RGB")
    r = file_name.rfind('.')
    out_name = file_name[:r] + '.webp'
    img.save(out_name, "webp")

def convert_to_webp(photo_id):
    db = inject('db')
    photo_rec = db(db.TblPhotos.id==photo_id).select().first()
    path = local_photos_folder(RESIZED) + photo_rec.photo_path
    jpg_to_webp(path)
    if photo_rec.oversize:
        path = local_photos_folder(ORIG) + photo_rec.photo_path
        jpg_to_webp(path)
    path = local_photos_folder(SQUARES) + photo_rec.photo_path
    jpg_to_webp(path)
    r = photo_rec.photo_path.rfind('.')
    webp_photo_path = photo_rec.photo_path[:r] + '.webp'
    photo_rec.update_record(webp_photo_path=webp_photo_path)

def get_photo_url(what, photo_rec, webp_supported):
    path = photos_folder(what)
    photo_path = photo_rec.photo_path_webp if photo_rec.photo_path_webp and webp_supported else photo_rec.photo_path
    return path + photo_path

def degrees_to_float(tup):
    degs, mins, secs = tup
    result = degs * 1.0 + mins * 1.0 / 60 + secs * 1.0 / 3600
    return round(result, 8)

def use_embedded_dates():
    db, NO_DATE = inject('db', 'NO_DATE')
    n = 0
    db(db.TblPhotos.photo_date==None).update(photo_date=NO_DATE)
    for prec in db((db.TblPhotos.photo_date==NO_DATE) & (db.TblPhotos.embedded_photo_date != None)).select():
        photo_date = prec.embedded_photo_date.date()
        prec.update_record(photo_date=photo_date, photo_date_dateunit='D', photo_date_datespan=1)
        n += 1
    return n

def calculate_photo_geo_info(prec):
    log_exception = inject('log_exception')
    folder = local_photos_folder(RESIZED)
    fname = folder + prec.photo_path
    if not os.path.exists(fname):
        return
    img = Image.open(fname)
    exif_data = get_exif_data(img)
    if 'GPSInfo' in exif_data:
        try:
            gps_info = exif_data['GPSInfo']
            lng = gps_info['GPSLongitude']
            lat = gps_info['GPSLatitude']
            longitude = degrees_to_float(lng)
            latitude = degrees_to_float(lat)
        except Exception as e:
            log_exception("getting photo geo data failed")
        else:
            prec.update_record(has_geo_info=True, longitude=longitude, latitude=latitude)
    else:
        prec.update_record(has_geo_info=False)

def calculate_geo_info():
    db = inject('db')
    db(db.TblPhotos.longitude!=None).update(has_geo_info=True)
    for prec in db(db.TblPhotos.has_geo_info==None).select(limitby=(0, 100), orderby=~db.TblPhotos.id):
        calculate_photo_geo_info(prec)
    n = db(db.TblPhotos.has_geo_info==None).count()
    return n

def recalculate_recognized():
    db = inject('db')
    db(db.TblPhotos.recognized==None).update(recognized=False)
    for pm in db(db.TblMemberPhotos).select(db.TblMemberPhotos.photo_id, db.TblMemberPhotos.photo_id.count(),groupby=db.TblMemberPhotos.photo_id):
        db(db.TblPhotos.id==pm.TblMemberPhotos.photo_id).update(recognized=True, handled=True)
    for pm in db(db.TblArticlePhotos).select(db.TblArticlePhotos.photo_id, db.TblArticlePhotos.photo_id.count(), groupby=db.TblArticlePhotos.photo_id):
        db(db.TblPhotos.id==pm.TblArticlePhotos.photo_id).update(recognized=True, handled=True)
    return "done"

def fix_date_ends():
    db, NO_DATE = inject('db', 'NO_DATE')
    next_day = datetime.timedelta(days=1)
    n = 0
    for rec in db((db.TblPhotos.photo_date!=NO_DATE)&(db.TblPhotos.photo_date_dateend==NO_DATE)).select():
        rec.update_record(photo_date_dateend=rec.photo_date + next_day)
        n += 1
    return f'{n} photos end-date fixed'


def resize_with_pad(im, target_width, target_height, color=(255,255,255,255)):
    '''
    Resize PIL image keeping ratio and using white background.
    '''
    target_ratio = target_height / target_width
    im_ratio = im.height / im.width
    if target_ratio > im_ratio:
        # It must be fixed by width
        resize_width = target_width
        resize_height = round(resize_width * im_ratio)
    else:
        # Fixed by height
        resize_height = target_height
        resize_width = round(resize_height / im_ratio)

    image_resize = im.resize((resize_width, resize_height), Image.ANTIALIAS)
    background = Image.new('RGBA', (target_width, target_height), color)
    offset = (round((target_width - resize_width) / 2), round((target_height - resize_height) / 2))
    background.paste(image_resize, offset)
    return background.convert('RGB')


def save_padded_photo(photo_path, target_photo_path, target_width=1200, target_height=630, color=(224,224,224,255)):
    im = Image.open(photo_path)
    padded = resize_with_pad(im, target_width, target_height, color)
    padded.save(target_photo_path, quality=90)
    r = target_photo_path.rfind('/')
    file_name = target_photo_path[r+1:]
    url = 'https://' + url_cards_folder() + f'padded_images/{file_name}'
    return url

def get_padded_photo_url(photo_id):
    db, request = inject('db', 'request')
    app = request.application
    app_area = app.split('__')[0]
    photo_rec = db(db.TblPhotos.id==photo_id).select().first()
    if not photo_rec:
        raise Exception(f"photo_id: {photo_id} - photo not found!")
    photo_path = local_photos_folder(RESIZED) + photo_rec.photo_path
    r = photo_path.rfind('.')
    ext = photo_path[r:]
    crc = photo_rec.crc
    file_name = f'{crc & 0xffffffff:x}{ext}'
    path = local_cards_folder() + 'padded_images/'
    dir_util.mkpath(path)
    target_photo_path = path + file_name
    padded_photo_url = save_padded_photo(photo_path, target_photo_path)
    return padded_photo_url

def save_qr_photo(data):
    db = inject('db')
    photo_id = int(data.photo_id)
    photo_rec = db(db.TblPhotos.id==photo_id).select().first()
    if not photo_rec:
        raise Exception(f"photo_id: {photo_id} - photo not found!")
    photo_path = local_photos_folder(ORIG) + photo_rec.photo_path
    im = Image.open(photo_path)
    if data.width:
        ppcm = im.width / int(data.width)
    else:
        ppcm = im.height / int(data.height)
    qrcode_size = 2.5
    margin = 0.5
    imq = qrcode.make(data.shortcut)
    qrcode_pixel_size = round(qrcode_size * ppcm)
    imq = imq.resize((qrcode_pixel_size, qrcode_pixel_size), Image.LANCZOS)
    margin_pixel_size = round(margin * ppcm)
    if data.position[0] == 'n':
        offset_y = margin_pixel_size
    else:
        offset_y = im.height - margin_pixel_size - imq.height
    if data.position[1] == 'w':
        offset_x = margin_pixel_size
    else:
        offset_x = im.width - margin_pixel_size - imq.width
    im.paste(imq, (offset_x, offset_y))
    img = im.convert('RGB')
    r = photo_path.rfind('.')
    ext = photo_path[r:]
    crc = photo_rec.crc
    file_name = f'{crc & 0xffffffff:x}{ext}'
    target_file_name = local_folder('temp') + file_name
    img.save(target_file_name)
    return url_folder('temp') + file_name

def calc_story_has_text():
    db = inject('db')
    q = (db.TblPhotos.deleted!=True) & (db.TblStories.id==db.TblPhotos.story_id)
    n = 0
    for rec in db(q).select():
        has_text = len(rec.TblStories.story) > 10
        if has_text:
            n += 1
        rec.TblPhotos.update_record(has_story_text=has_text)
    return f"{n} photos have story text"

def str_to_image(binVal: str):
    blob = to_bytes(binVal)
    crc = zlib.crc32(blob)
    blob = array.array('B', [x for x in map(ord, binVal)]).tobytes()
    stream = BytesIO(blob)
    img = Image.open(stream)
    return (img, crc)
