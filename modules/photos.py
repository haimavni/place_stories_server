import PIL
from PIL import Image
from gluon.storage import Storage
from injections import inject
import os
from distutils import dir_util

def get_image_info(image_path):
    img = Image.open(image_path)
    width, height = img.size
    faces = []
    return Storage(width=width, height=height, faces=faces)


def scan_all_unscanned_photos():
    db, request, comment = inject('db', 'request', 'comment')
    q = (db.TblPhotos.width == 0) & (db.TblPhotos.photo_missing == False)
    to_scan = db(q).count()
    chunk = 100
    folder = 'applications/' + photos_folder()
    while True:
        comment('started scanning chunk of photos')
        lst = db(q).select(limitby=(0, chunk))
        if len(lst) == 0:
            comment('No unscanned photos were found!')
            return dict(message='No unscanned photos were found!', to_scan=to_scan)
        for rec in lst:
            fname = folder + rec.LocationInDisk
            if not os.path.exists(fname):
                rec.update_record(photo_missing=True)
                continue
            inf = get_image_info(fname)
            width, height, faces = inf.width, inf.height, inf.faces
            rec.update_record(width=width, height=height)
            for face in faces:
                x, y, w, h = face
                db.TblMemberPhotos.insert(Photo_id=rec.id, x=x, y=y, w=w, h=h) # for older records, merge with record photo_id-member_id
        db.commit()
        missing = db(db.TblPhotos.photo_missing==True).count()
        done = db(db.TblPhotos.width>0).count()
        total = db(db.TblPhotos).count()
    return dict(done=done, total=total, missing=missing, to_scan=to_scan)

def photos_folder(what="orig"): 
    #what may be orig, squares,images or profile_photos. (images is for customer-specific images such as logo)
    #app appears twice: one to reach static, the other is to separate different customers
    request = inject('request')
    return '{app}/static/gb_photos/{app}/photos/{what}/'.format(app=request.application, what=what)

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
    slides = [dict(photo_id=rec.id, src=folder + rec.LocationInDisk, width=rec.width, height=rec.height, title=rec.Description) for rec in lst]
    return slides

def crop(input_path, output_path, face, size=100):
    img = Image.open(input_path)
    area = (face.x - face.r, face.y - face.r, face.x + face.r, face.y + face.r)
    cropped_img = img.crop(area)
    resized_img = cropped_img.resize((size, size), Image.LANCZOS)
    resized_img.save(output_path)

def crop_square(img_src, width, height, side_size):
    if width > hight:
        x = (width - height) / 2
        x1 = x + width
        y = 0,
        y1 = height
    else:
        y = (height - width) / 2
        y1 = y + height
        x = 0
        x1 = width
    input_path = photos_folder() + img_src
    output_path = photos_folder("squares") + os.path.dirname(image_src)
    dir_util.mkpath(output_path)
    img = Image.open(photos_folder() + img_src)
    area = (x, y, x1, y1)
    cropped_img = img.crop(area)
    resized_img = cropped_img.resize((side_size, side_size), Image.LANCZOS)
    resized_img.save(output_path)

