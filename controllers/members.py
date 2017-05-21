import stories_manager
from gluon.storage import Storage
from my_cache import Cache
import ws_messaging
from http_utils import json_to_storage
import datetime
import os
from dal_utils import insert_or_update
from photos import get_slides_from_photo_list


@serve_json
def member_list(vars):
    return dict(member_list=get_member_names(vars.visible_only, vars.gender))


def get_member_names(visible_only=None, gender=None):
    q = (db.TblMembers.id > 0)
    if visible_only:
        q &= (db.TblMembers.visible == True)
    if gender:
        q &= (db.TblMembers.gender == gender)

    lst = db(q).select(db.TblMembers.first_name,
                       db.TblMembers.last_name,
                       db.TblMembers.former_first_name,
                       db.TblMembers.former_last_name,
                       db.TblMembers.NickName,
                       db.TblMembers.gender,
                       db.TblMembers.visible,
                       db.TblMembers.facePhotoURL,
                       orderby=[db.TblMembers.last_name, db.TblMembers.first_name])
    arr = [Storage(id=rec.id,
                   name=member_display_name(rec, full=True),
                   gender=rec.gender,
                   facePhotoURL=rec.facePhotoURL or 'http://' + request.env.http_host + "/gbs/static/images/dummy_face.png") for rec in lst]
    return arr

def get_member_names(visible_only=None, gender=None):
    q = (db.TblMembers.id > 0)
    if visible_only:
        q &= (db.TblMembers.visible == True)
    if gender:
        q &= (db.TblMembers.gender == gender)

    lst = db(q).select()
    arr = [Storage(id=rec.id,
                   name=member_display_name(rec, full=True),
                   gender=rec.gender,
                   facePhotoURL=rec.facePhotoURL or 'http://' + request.env.http_host  + "/gbs/static/images/dummy_face.png") for rec in lst]
    return arr

def older_display_name(rec, full):
    s = rec.Name or ''
    if full and rec.FormerName:
        s += ' ({})'.format(rec.FormerName)
    if full and rec.NickName:
        s += ' - {}'.format(rec.NickName)
    return s

def member_display_name(rec=None, member_id=None, full=True):
    rec = rec or get_member_rec(member_id)
    if not rec:
        return ''
    if not rec.first_name:
        return older_display_name(rec, full)
    s = rec.first_name
    if full and rec.former_first_name:
        s += ' ({})'.format(rec.former_first_name)
    s += ' ' + rec.last_name
    if full and rec.former_last_name:
        s += ' ({})'.format(rec.former_last_name)
    if rec.NickName:
        s += ' - {}'.format(rec.NickName)
    return s

def get_member_rec(member_id, member_rec=None):
    if member_rec:
        rec = member_rec #used when initially all members are loaded into the cache
    elif not member_id:
        return None
    else:
        recs = db(db.TblMembers.id==member_id).select()
        rec = recs.render(0)
        rec = db(db.TblMembers.id==member_id).select().first()
    if not rec:
        return None
    rec = Storage(rec.as_dict())
    rec.full_name = member_display_name(rec, full=True)
    rec.name = member_display_name(rec, full=False)
    return rec

def get_parents(member_id):
    member_rec = get_member_rec(member_id)
    pa = member_rec.father_id
    ma = member_rec.mother_id
    pa_rec = get_member_rec(pa)
    ma_rec = get_member_rec(ma)
    parents = Storage()
    if pa_rec:
        parents.pa = pa_rec
    if ma_rec:
        parents.ma = ma_rec
    return parents

def get_siblings(member_id):
    parents = get_parents(member_id)
    if not parents:
        return None
    pa, ma = parents.pa, parents.ma
    q = db.TblMembers.id!=member_id
    if pa:
        lst1 = db(q & (db.TblMembers.father_id==pa.id)).select() if pa else []
        lst1 = [r.id for r in lst1]
    else:
        lst1 = []
    if ma:
        lst2 = db(q & (db.TblMembers.mother_id==ma.id)).select() if ma else []
        lst2 = [r.id for r in lst2]
    else:
        lst2 = []
    lst = list(set(lst1 + lst2)) #make it unique
    lst = [get_member_rec(id) for id in lst]
    return lst

def get_children(member_id):
    member_rec = get_member_rec(member_id)
    if member_rec.gender=='F' :
        q = db.TblMembers.mother_id==member_id
    elif member_rec.gender=='M':
        q = db.TblMembers.father_id==member_id
    else:
        return None #error!
    lst = db(q).select(db.TblMembers.id)
    lst = [get_member_rec(rec.id) for rec in lst]
    return lst
    ###return [Storage(rec.as_dict()) for rec in lst] more efficient but not as safe

def get_spouses(member_id):
    children = get_children(member_id)
    member_rec = get_member_rec(member_id)
    if member_rec.gender == 'F':
        spouses = [child.father_id for child in children]
    elif member_rec.gender == 'M':
        spouses = [child.mother_id for child in children]
    else:
        spouses = [] ##error
    spouses = [sp for sp in spouses if sp]  #to handle incomplete data
    spouses = list(set(spouses))
    return [get_member_rec(m_id) for m_id in spouses]

def get_family_connections(member_info):
    return Storage(
        parents=get_parents(member_info.id),
        siblings=get_siblings(member_info.id),
        spouses=get_spouses(member_info.id),
        children=get_children(member_info.id),
    )

def get_member_images(member_id):
    lst = db((db.TblMemberPhotos.Member_id==member_id) & \
             (db.TblPhotos.id==db.TblMemberPhotos.Photo_id) & \
             (db.TblPhotos.width>0)).select()
    return [dict(id=rec.TblPhotos.id, path=request.application + '/static/gb_photos/' + rec.TblPhotos.LocationInDisk) for rec in lst]

def get_member_slides(member_id):
    q = (db.TblMemberPhotos.Member_id==member_id) & \
        (db.TblPhotos.id==db.TblMemberPhotos.Photo_id)
    return get_slides_from_photo_list(q)

