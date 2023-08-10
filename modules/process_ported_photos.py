from photos_support import *
import binascii
import crc_calc
import shutil
from injections import inject
from folders import RESIZED, ORIG, SQUARES, PROFILE_PHOTOS

class ProcessPortedPhotos:

    def process_photo(self, photo_id):
        comment = inject('comment')
        comment(f"enter process_photo {photo_id}")
        auth, comment, log_exception, db, STORY4PHOTO, NO_DATE = inject('auth', 'comment', 'log_exception', 'db',
                                                                        'STORY4PHOTO', 'NO_DATE')
        prec = db(db.TblPhotos.id==photo_id).select().first()
        file_name = local_photos_folder(ORIG) + prec.photo_path
        with open(file_name, 'rb') as f:
            blob = f.read()
        crc = zlib.crc32(blob)
        today = datetime.date.today()
        month = str(today)[:-3]
        sub_folder = 'ported/' + month + '/'
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
                        fname = local_photos_folder(ORIG) + prec.photo_path
                        img.save(fname, quality=95)  ###, exif=img.info['exif'])
            if 'DateTimeDigitized' in exif_data:
                s = exif_data['DateTimeDigitized']
                try:
                    comment(f"embedded date is {s}")
                    embedded_photo_date = datetime.datetime.strptime(s, '%Y:%m:%d %H:%M:%S')
                except Exception as e:
                    log_exception('getting photo embedded date failed')

            width, height = img.size
            comment(f"-----------width is {width} and height is {height}-------")
            if not width:
                comment("==================img size is zero=========")
                width, height = (799, 601)
            square_img = crop_to_square(img, width, height, 256)
            if square_img:
                path = local_photos_folder(SQUARES) + sub_folder
                dir_util.mkpath(path)
                fname = file_name.replace('/oversize/', '/squares/')
                square_img.save(fname)
                fix_owner(path)
                fix_owner(fname)
                got_square = True
            else:
                got_square = False
            # change: all originals are saved in ORIG which should be renamed RESIZED. orig needs to be changed to "resized"
            oversize = False
            oversize_path = local_photos_folder(ORIG) + sub_folder
            dir_util.mkpath(oversize_path)
            oversize_fname = file_name.replace('/orig/', '/oversize/')
            shutil.copyfile(file_name, oversize_fname)
            fix_owner(oversize_path)
            fix_owner(oversize_fname)
            if height > MAX_HEIGHT or width > MAX_WIDTH:
                oversize = True
            width, height = resized(width, height)
            comment(f"after resized-----------width is {width} and height is {height}-------")
            img = img.resize((width, height), Image.LANCZOS)
            path = local_photos_folder(RESIZED) + sub_folder
            img.save(file_name, quality=95)  ###, exif=img.info['exif'])
            fix_owner(path)
            fix_owner(file_name)
            dhash_value = dhash_photo(img=img)
        except Exception as e:
            log_exception("saving photo {} failed".format(prec.original_file_name))
            return Storage(failed=1)
        # sm = Stories()
        # story_info = sm.get_empty_story(used_for=STORY4PHOTO, story_text="", name=prec.original_file_name)
        # result = sm.add_story(story_info)
        # story_id = result.story_id

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
        comment(f"just before update record. {width}x{height}")
        prec.update_record(
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
            dhash=dhash_value,
            oversize=oversize,
            photo_missing=False,
            deleted=False,
            random_photo_key=random.randint(1, 101)
        )
        db.commit()
        return Storage(photo_id=photo_id)

