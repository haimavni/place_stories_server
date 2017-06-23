import PIL
from PIL import Image
from gluon.storage import Storage
from injections import inject
import os

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
    folder = request.application + '/static/gb_photos/'
    while True:
        comment('Started chunk of photos')
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

def fix_photo_location_case():
    db = inject('db')
    for rec in db(db.TblPhotos).select():
        low_location = rec.LocationInDisk.lower()
        if low_location != rec.LocationInDisk:
            rec.update_record(LocationInDisk=low_location)

def photos_folder():
    request = inject('request')
    return '/' + request.application + '/static/gb_photos/'

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

def save_resized_image(img_src, w, h, folder):
    img = Image.open('/static/gb_photos/originals/' + img_src)
    new_img = img.resize((w,h), Image.LANCZOS)
    new_img.save('/static/gb_photos/{f}/{i}'.format(f=folder, i=img_src), "JPEG", optimize=True)

def crop(input_path, output_path, face):
    path = os.getcwd()
    img = Image.open(input_path)
    area = (face.x - face.r, face.y - face.r, face.x + face.r, face.y + face.r)
    cropped_img = img.crop(area)
    resized_img = cropped_img.resize((100, 100), Image.LANCZOS)
    resized_img.save(output_path)
