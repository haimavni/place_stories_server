import PIL
from PIL import Image, ImageFile
from injections import inject
import os
import datetime
from distutils import dir_util
import zlib
from cStringIO import StringIO
from date_utils import datetime_from_str
from gluon.storage import Storage

MAX_WIDTH = 1200
MAX_HEIGHT = 800

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

def save_uploaded_photo(file_name, blob, user_id, sub_folder=None):
    auth, comment, log_exception, db = inject('auth', 'comment', 'log_exception', 'db')
    user_id = user_id or auth.current_user()
    crc = zlib.crc32(blob)
    cnt = db(db.TblPhotos.crc==crc).count()
    if cnt > 0:
        return 'duplicate'
    original_file_name, ext = os.path.splitext(file_name)
    file_name = '{crc:x}{ext}'.format(crc=crc & 0xffffffff, ext=ext)
    comment('start saving {}', original_file_name)
    today = datetime.date.today()
    month = str(today)[:-3]
    if not sub_folder:
        sub_folder = sub_folder or 'uploads/' + month + '/'
    path = local_photos_folder() + sub_folder
    dir_util.mkpath(path)
    try:
        stream = StringIO(blob)
        img = Image.open(stream)
        exif = img._getexif()
        if exif:
            photo_date = exif[36867]
        else:
            photo_date = None
        width, height = img.size
        square_img = crop_to_square(img, width, height, 256)
        if square_img:
            path = local_photos_folder("squares") + sub_folder
            dir_util.mkpath(path)
            square_img.save(path + file_name)
            got_square = True
        else:
            got_square = False
        oversize = False
        if height > MAX_HEIGHT or width > MAX_WIDTH:
            oversize = True
            path = local_photos_folder("oversize") + sub_folder
            dir_util.mkpath(path)
            img.save(path + file_name)
            width, height = resized(width, height)
            img = img.resize((width, height), Image.LANCZOS)
        path = local_photos_folder() + sub_folder
        if photo_date:
            photo_date = datetime_from_str(photo_date, date_only=True)
        elif os.path.isfile(path + file_name):
            photo_date = modification_date(path + file_name)
        else:
            photo_date = None
        img.save(path + file_name)
    except Exception, e:
        log_exception("saving photo {} failed".format(original_file_name))
        return 'failed'

    photo_id = db.TblPhotos.insert(
        photo_path=sub_folder + file_name,
        original_file_name=original_file_name,
        Name=original_file_name,
        uploader=user_id,
        upload_date=datetime.datetime.now(),
        photo_date=photo_date,
        width=width,
        height=height,
        crc=crc,
        oversize=oversize,
        photo_missing=False
    )
    return photo_id

def get_image_info(image_path):
    img = Image.open(image_path)
    width, height = img.size
    faces = []
    return Storage(width=width, height=height, faces=faces)

def fit_size(rec):
    db, log_exception = inject('db', 'log_exception')
    fname = local_photos_folder() + rec.photo_path
    try:
        img = Image.open(fname)
        oversize_file_name = local_photos_folder("oversize") + rec.photo_path
        oversize_path, f = os.path.split(oversize_file_name)
        dir_util.mkpath(oversize_path)
        img.save(oversize_file_name)
        width, height = resized(rec.width, rec.height)
        img = img.resize((width, height), Image.LANCZOS)
        img.save(fname)
        rec.update_record(width=width, height=height)
    except Exception, e:
        log_exception("resizing file {} failed.".format(rec.photo_path))
        rec.update_record(photo_missing=True)
        return False
    return True

def fit_all_sizes():
    db, request, comment = inject('db', 'request', 'comment')
    comment('started fitting size for chunk of photos')
    q = (db.TblPhotos.width > MAX_WIDTH) | (db.TblPhotos.height > MAX_HEIGHT)
    q &= (db.TblPhotos.photo_missing != True)
    chunk = 100
    num_failed = 0
    while True:
        n = db(q).count()
        comment('started fitting size for chunk of photos. {} more to go.'.format(n))
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
    q = (db.TblPhotos.crc==None) & (db.TblPhotos.photo_missing == False)
    to_scan = db(q).count()
    comment("{} photos still unscanned", to_scan)
    failed_crops = 0
    chunk = 100
    folder = local_photos_folder()
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
                db.TblMemberPhotos.insert(Photo_id=rec.id, x=x, y=y, w=w, h=h) # for older records, merge with record photo_id-member_id
        db.commit()
        missing = db(db.TblPhotos.photo_missing==True).count()
        done = db(db.TblPhotos.width>0).count()
        total = db(db.TblPhotos).count()
    return dict(done=done, total=total, missing=missing, to_scan=to_scan, failed_crops=failed_crops)

def photos_folder(what="orig"): 
    #what may be orig, squares,images or profile_photos. (images is for customer-specific images such as logo)
    #app appears twice: one to reach static, the other is to separate different customers
    request = inject('request')
    app = request.application.split('__')[0]
    return 'http://{host}/{app}/static/gb_photos/{app}/photos/{what}/'.format(host=request.env.http_host, app=app, what=what)

def images_folder():
    request = inject('request')
    app = request.application.split('__')[0]  ## we want gbs__dev, gbs__test etc. all to use the same data
    return 'http://{host}/{app}/static/gb_photos/{app}/images/'.format(host=request.env.http_host, app=app)

def local_photos_folder(what="orig"): 
    #what may be orig, squares,images or profile_photos. (images is for customer-specific images such as logo)
    request = inject('request')
    app = request.application.split('__')[0]  ## we want gbs__dev, gbs__test etc. all to use the same data
    return '/gb_photos/{app}/photos/{what}/'.format(app=app, what=what)

def get_slides_from_photo_list(q):
    db = inject('db')
    q &= (db.TblPhotos.width > 0)
    db = inject('db')
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

    folder = photos_folder()
    slides = [dict(photo_id=rec.id, src=folder + rec.photo_path, width=rec.width, height=rec.height, title=rec.Description or rec.Name) for rec in lst]
    return slides

def crop(input_path, output_path, face, size=100):
    img = Image.open(input_path)
    area = (face.x - face.r, face.y - face.r, face.x + face.r, face.y + face.r)
    cropped_img = img.crop(area)
    resized_img = cropped_img.resize((size, size), Image.LANCZOS)
    resized_img.save(output_path)

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
    path = path.replace('orig', 'squares')
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

def add_photos_from_drive(sub_folder):
    folder = local_photos_folder("orig")
    root_folder = folder + sub_folder
    for root, dirs, files in os.walk(root_folder, topdown=True):
        print("there are", len(files), "files in", root)
        for file_name in files:
            path = root + '/' + file_name
            with open(path, 'r') as f:
                blob = f.read()
            result = save_uploaded_photo(file_name, blob, 1, sub_folder=sub_folder)
            if result in ('failed', 'duplicate'):
                continue
            #delete the file. it has been saved using crc as name and was possibly resized
            os.remove(path)


