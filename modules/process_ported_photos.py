from photos_support import *
from injections import inject
from folders import RESIZED, ORIG, SQUARES, PROFILE_PHOTOS
import os
from distutils import dir_util

class ProcessPortedPhotos:
    def __init__(self):
        self.db = inject("db")

    def log_it(self, s):
        my_log = inject("my_log")
        my_log(s, file_name="process_photos.log")

    def process_photo(self, photo_id):
        log_exception, db, NO_DATE = inject('log_exception', 'db', 'NO_DATE')
        self.log_it(f"enter process_photo {photo_id}")
        photo_rec = db(db.TblPhotos.id==photo_id).select().first()
        orig_file_name = local_photos_folder(ORIG) + photo_rec.photo_path
        try:
            with open(orig_file_name, 'rb') as f:
                blob = f.read()
        except Exception as e:
            photo_rec.update_record(photo_missing=True)
            self.log_it(f"file {orig_file_name} could not be opened")
            return
        crc = zlib.crc32(blob)
        #rename file using crc
        file_name = local_photos_folder(ORIG) + self.rename_file(photo_rec.photo_path, crc)
        square_file_name = file_name.replace(f"/{ORIG}/", f"/{SQUARES}/")
        resized_file_name = file_name.replace(f"/{ORIG}/", f"/{RESIZED}/")
        photo_rec.update_record(crc=crc, photo_path=)
        stream = BytesIO(blob)
        img = Image.open(stream)
        try:
            exif_data = self.use_exif_data(img)
        except Exception as e:
            exif_data = None
            log_exception("exif data could not be obtained")
        if exif_data:
            photo_rec.update_record(
                       latitude=exif_data.latitude,
                       longitude=exif_data.longitude,
                       zoom=exif_data.zoom,
                       has_geo_info=exif_data.longitude!=None,
                       embedded_photo_date=exif_data.embedded_photo_date)
            photo_date = photo_rec.photo_date
            if exif_data.embedded_photo_date:
                if (not photo_date) or \
                    (photo_date == NO_DATE) or \
                    (photo_rec.photo_date.year == exif_data.embedde_photo_date.year):
                    photo_date = exif_data.embedded_photo_date.date()
                    photo_date_dateend = photo_date + datetime.timedelta(days=1)
                    photo_rec.update_record(photo_date=photo_date, 
                                            photo_date_dateend=photo_date_dateend,
                                            photo_date_dateunit = 'D',
                                            photo_date_datespan = 1
                                            )
        try:
            width, height = img.size
            self.log_it(f"-----------width is {width} and height is {height}-------")
            if not width:
                self.log_it("==================img size is zero=========")
                width, height = (799, 601)
            square_img = crop_to_square(img, width, height, 256)
            if square_img:
                path, fn = os.path.split(square_file_name)
                dir_util.mkpath(path)
                square_img.save(square_file_name)
                fix_owner(path)
                fix_owner(square_file_name)
            else:
                self.log_it(f"Could not create square for photo {photo_id}")
            path, fn = os.path.split(file_name)
            fix_owner(path)
            fix_owner(file_name)
            if height > MAX_HEIGHT or width > MAX_WIDTH:
                oversize = True
            else:
                oversize = False
            width, height = resized(width, height)
            self.log_it(f"after resized-----------width is {width} and height is {height}-------")
            img = img.resize((width, height), Image.LANCZOS)
            path, fn = os.path.split(resized_file_name)
            dir_util.mkpath(path)
            img.save(resized_file_name, quality=95)  ###, exif=img.info['exif'])
            path, fn = os.path.split(resized_file_name)
            fix_owner(path)
            fix_owner(resized_file_name)
            dhash_value = dhash_photo(img=img)
        except Exception as e:
            log_exception(f"saving photo {photo_rec.original_file_name} failed")
            return Storage(failed=1)
        self.log_it(f"just before update record. {width}x{height}")
        photo_rec.update_record(
            upload_date=datetime.datetime.now(),
            width=width,
            height=height,
            dhash=dhash_value,
            oversize=oversize,
            photo_missing=False,
            deleted=False,
            random_photo_key=random.randint(1, 101)
        )
        db.commit()
        return Storage(photo_id=photo_id)
    
    def rename_file_name(self, fname, crc):
        path, name = os.path.split(fname)
        name, ext = os.path.splitext(name)
        file_name = f'{path}{crc & 0xffffffff:x}{ext}'
        src = local_photos_folder(ORIG) + fname
        dst = local_photos_folder(ORIG) + file_name
        os.rename(src, dst)
        return file_name
    
    def process_all_unprocessed_photos(self, limit=None):
        limit = limit or 99999
        db = self.db
        
        lst = db((db.TblPhotos.width==0)|(db.TblPhotos.photo_missing==True)).select(db.TblPhotos.id, limitby=(0, limit))
        for prec in lst:
            self.process_photo(prec.id)
        left_to_process = db(db.TblPhotos.width==0).count()
        db.commit()
        return f"{left_to_process} photos remain to be processed"

    def use_exif_data(self, img):
        log_exception = inject("log_exception")
        latitude = None
        longitude = None
        zoom = None
        embedded_photo_date = None
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
            s = exif_data['DateTimeDigitized']
            try:
                self.log_it(f"embedded date is {s}")
                embedded_photo_date = datetime.datetime.strptime(s, '%Y:%m:%d %H:%M:%S')
            except Exception as e:
                log_exception('getting photo embedded date failed')
        return Storage(img=img,
                       latitude=latitude,
                       longitude=longitude,
                       zoom=zoom,
                       embedded_photo_date=embedded_photo_date)


