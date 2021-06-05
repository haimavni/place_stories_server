from gluon._compat import to_bytes
from photos_support import *
import binascii

def add_photo_info(photo_id):
    auth, comment, log_exception, db, STORY4PHOTO, NO_DATE = inject('auth', 'comment', 'log_exception', 'db',
                                                                    'STORY4PHOTO', 'NO_DATE')
    prec = db(db.TblPhotos.id==photo_id).select().first()
    file_name = local_photos_folder() + prec.photo_path
    with open(file_name, 'rb') as f:
        blob = f.read()
    crc = zlib.crc32(blob)
    crc1 = binascii.crc32(blob)
    comment(f"crc: {crc:x}, crc1: {crc1:x}")

    comment(f"file {file_name} prec.crc: {prec.crc:x} crc: {crc:x}, len(blob): {len(blob)}")
    today = datetime.date.today()
    month = str(today)[:-3]
    sub_folder = 'uploads/' + month + '/'
    latitude = None
    longitude = None
    zoom = None
    embedded_photo_date = None
    try:
        ###blob = array.array('B', [x for x in map(ord, s)]).tobytes()
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
                    fname = local_photos_folder("oversize") + prec.photo_path
                    img.save(fname, quality=95)  ###, exif=img.info['exif'])
        if 'DateTimeDigitized' in exif_data:
            s = exif_data['DateTimeDigitized']
            try:
                comment(f"embedded date is {s}")
                embedded_photo_date = datetime.datetime.strptime(s, '%Y:%m:%d %H:%M:%S')
            except Exception as e:
                log_exception('getting photo embedded date failed')

        width, height = img.size
        square_img = crop_to_square(img, width, height, 256)
        if square_img:
            path = local_photos_folder("squares") + sub_folder
            dir_util.mkpath(path)
            fname = file_name.replace('/orig/', '/squares/')
            square_img.save(fname)
            fix_owner(path)
            fix_owner(fname)
            got_square = True
        else:
            got_square = False
        oversize = False
        if height > MAX_HEIGHT or width > MAX_WIDTH:
            oversize = True
            path = local_photos_folder("oversize") + sub_folder
            dir_util.mkpath(path)
            fname = file_name.replace('/orig/', '/oversize/')
            img.save(fname, quality=95)  ###, exif=img.info['exif'])
            fix_owner(path)
            fix_owner(fname)
            width, height = resized(width, height)
            img = img.resize((width, height), Image.LANCZOS)
        elif height < MAX_HEIGHT and width < MAX_WIDTH:
            width, height = resized(width, height)
            img = img.resize((width, height), Image.LANCZOS)
        path = local_photos_folder() + sub_folder
        ###exif = img.info['exif'] if img.info and 'exif' in img.info e
        img.save(file_name, quality=100)  ###, exif=img.info['exif'])
        fix_owner(path)
        fix_owner(file_name)
        dhash_value = dhash_photo(img=img)
    except Exception as e:
        log_exception("saving photo {} failed".format(prec.original_file_name))
        return Storage(failed=1)
    sm = Stories()
    story_info = sm.get_empty_story(used_for=STORY4PHOTO, story_text="", name=prec.original_file_name)
    result = sm.add_story(story_info)
    story_id = result.story_id

    if embedded_photo_date:
        photo_date = embedded_photo_date.date()
        photo_date_dateend = photo_date + datetime.timedelta(days=1)
        photo_date_dateunit = 'D'
        photo_date_datespan = 1
    else:
        photo_date = NO_DATE
        photo_date_dateend = NO_DATE
        photo_date_dateunit = 'Y'
        photo_date_datespan = 1
    has_geo_info = longitude is not None
    prec.update_record(
    ###photo_id = db.TblPhotos.insert(
        embedded_photo_date=embedded_photo_date,
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

