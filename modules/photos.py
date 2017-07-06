import PIL
from PIL import Image
from gluon.storage import Storage
from injections import inject
import os
from distutils import dir_util
import zlib
from cStringIO import StringIO

MAX_WIDTH = 1200
MAX_HEIGHT = 800

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

    
def save_uploaded_photo(file_name, blob, path_tail):
    stream = StringIO(blob)
    img = Image.open(stream)
    width, height = img.size
    square_img = crop_to_square(img, width, height, 256)
    if square_img:
        path = local_photos_folder("squares") + path_tail
        square_img.save(path + file_name)
        got_square = True
    else:
        got_square = False
    oversize = False
    if height > MAX_HEIGHT or width > MAX_WIDTH:
        oversize = True
        path = local_photos_folder("oversize") + path_tail
        dir_util.mkpath(path)
        img.save(path + file_name)
        width, height = resized(width, height)
        img = img.resize((width, height), Image.LANCZOS)
    path = local_photos_folder() + path_tail
    img.save(path + file_name)
    return Storage(oversize=oversize, got_square=got_square, width=width, height=height)



def get_image_info(image_path):
    img = Image.open(image_path)
    width, height = img.size
    faces = []
    return Storage(width=width, height=height, faces=faces)

def scan_all_unscanned_photos():
    db, request, comment = inject('db', 'request', 'comment')
    q = (db.TblPhotos.crc==None) & (db.TblPhotos.photo_missing == False)
    to_scan = db(q).count()
    failed_crops = 0
    chunk = 100
    folder = local_photos_folder()
    while True:
        comment('started scanning chunk of photos')
        lst = db(q).select(limitby=(0, chunk))
        if len(lst) == 0:
            comment('No unscanned photos were found!')
            return dict(message='No unscanned photos were found!', to_scan=to_scan)
        for rec in lst:
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
    return 'http://{host}/{app}/static/gb_photos/{app}/photos/{what}/'.format(host=request.env.http_host, app=request.application, what=what)

def local_photos_folder(what="orig"): 
    #what may be orig, squares,images or profile_photos. (images is for customer-specific images such as logo)
    request = inject('request')
    return '/gb_photos/{app}/photos/{what}/'.format(app=request.application, what=what)

def get_slides_from_photo_list(q):
    db = inject('db')
    q &= (db.TblPhotos.width > 0)
    db = inject('db')
    lst = db(q).select()
    if not lst:
        return []
    if 'TblPhotos' in lst[0]:
        lst = [rec.TblPhotos for rec in lst]
    folder = photos_folder()
    slides = [dict(photo_id=rec.id, src=folder + rec.photo_path, width=rec.width, height=rec.height, title=rec.Description) for rec in lst]
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

