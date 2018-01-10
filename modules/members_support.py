from injections import inject
from gluon.storage import Storage
from photos import photos_folder

def get_member_rec(member_id, member_rec=None, prepend_path=False):
    db = inject('db')
    if member_rec:
        rec = member_rec #used when initially all members are loaded into the cache
    elif not member_id:
        return None
    else:
        rec = db(db.TblMembers.id==member_id).select().first()
    if not rec:
        return None
    if rec.deleted:
        return None
    rec = Storage(rec.as_dict())
    rec.full_name = member_display_name(rec, full=True)
    rec.name = member_display_name(rec, full=False)
    if prepend_path :
        rec.facePhotoURL = photos_folder('profile_photos') + (rec.facePhotoURL or 'dummy_face.png')
    return rec

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
    s = rec.first_name + ' ' + rec.last_name
    if full and (rec.former_first_name or rec.former_last_name):
        s += ' ('
        if rec.former_first_name:
            s += rec.former_first_name
        if rec.former_last_name:
            if rec.former_first_name:
                s += ' '
            s += rec.former_last_name
        s += ')'     
    if rec.NickName:
        s += ' - {}'.format(rec.NickName)
    return s

