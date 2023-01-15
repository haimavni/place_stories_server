from folders import *
import zlib
from io import StringIO
import csv
from PIL import Image, ImageFile
from photos_support import save_uploaded_photo, photos_folder, timestamped_photo_path, str_to_image
from members_support import get_photo_topics
from topics_support import *
import ws_messaging
from admin_support import access_manager
import stories_manager
from gluon.storage import Storage
from date_utils import update_record_dates, get_all_dates
from send_email import email
from gluon._compat import to_bytes
import os
import re

@serve_json
def get_group_list(vars):
    lst = db(db.TblGroups.topic_id == db.TblTopics.id).select()
    lst = [dict(id=r.TblGroups.id, title=r.TblTopics.name, description=r.TblGroups.description, logo_url=get_logo_url(r.TblGroups.id)) for r in lst]
    return dict(group_list = lst)

@serve_json
def get_contact_list(vars):
    lst = db(db.TblGroupContacts.deleted!=True).select()
    lst = [dict(id=r.id, group_id=r.group_id, email=r.email, first_name=r.first_name, last_name=r.last_name) for r in lst]
    return dict(contact_list = lst)

@serve_json
def add_or_update_group(vars):
    group_id = vars.id
    if group_id:
        rec = db(db.TblGroups.id==group_id).select().first()
        rename_a_topic(rec.topic_id, vars.title) 
        rec.update_record(description=vars.description)
        #todo: rename topic! (or use only topic_id)
    else:
        topic_id = add_a_topic(vars.title)
        group_id = db.TblGroups.insert(topic_id=topic_id, description=vars.description)
    group_data = dict(title=vars.title, description=vars.description, id=group_id, logo_url=get_logo_url(group_id))
    return dict(group_data=group_data)

@serve_json
def add_or_update_contact(vars):
    contact_id = vars.id
    group_id = vars.group_id
    if contact_id:
        rec = db(db.TblGroupContacts.id==contact_id).select().first()
        rec.update_record(email=vars.email, first_name=vars.first_name, last_name=vars.last_name)
    else:
        if not db((db.TblGroupContacts.email==vars.email) & (db.TblGroupContacts.deleted != True)).isempty():
            raise User_Error("groups.duplicate-contact")
        rec = db((db.TblGroupContacts.email==vars.email) & (db.TblGroupContacts.deleted == True)).select().first()
        if rec:
            rec.update_record(deleted=False)
            contact_id = rec.id
        else:
            contact_id = db.TblGroupContacts.insert(group_id=group_id, email=vars.email, first_name=vars.first_name, last_name=vars.last_name)
    contact_data = dict(group_id=group_id, id=vars.id, first_name=vars.first_name, last_name=vars.last_name, email=vars.email)
    return dict(contact_data=contact_data)

@serve_json
def remove_contact(vars):
    contact_id = int(vars.contact_id)
    group_id = int(vars.group_id)
    rec = db(db.TblGroupContacts.id==contact_id).select().first()
    rec.update_record(deleted=True)
    return dict()

@serve_json
def get_group_info(vars):
    group_id = vars.group_id
    logo_url = get_logo_url(group_id)
    rec = db(db.TblGroups.id==group_id).select().first()
    if not rec:
        raise Exception("No group created yet.")
    return dict(title=topic_name(rec.topic_id),
                description=rec.description,
                logo_url=logo_url)

@serve_json
def upload_group_logo(vars):
    fil = vars.file
    group_id=fil.info.group_id
    file_name = save_uploaded_logo(fil.name, fil.BINvalue, group_id)
    return dict(upload_result=dict(), logo_url=get_logo_url(group_id))

@serve_json
def upload_contacts(vars):
    stream = StringIO(vars.file.BINvalue)
    added = 0
    group_id = vars.file.info.group_id
    for rec in get_records_from_csv_stream(stream):
        email, first_name, last_name = rec[:3] 
        q = (db.TblGroupContacts.group_id==group_id) & (db.TblGroupContacts.email==email)
        cont_rec =  db(q).select().first()
        if cont_rec:
            if cont_rec.deleted:
                added += 1
            cont_rec.update_record(deleted=False)
        else:
            added += 1
            db.TblGroupContacts.insert(email=email, first_name=first_name, last_name=last_name, group_id=group_id)
    ws_messaging.send_message(key='CONTACTS-FILE-UPLOADED', group='ALL', added=added)
    return dict(upload_result=dict())

def get_records_from_csv_stream(csvfile):
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    next(reader)     #skip header
    for row in reader:
        yield row
    

@serve_json
def delete_group(vars):
    db(db.TblGroups.id==vars.group_id).delete()
    return dict()

@serve_json
def upload_photo(vars):
    user_id = vars.user_id or auth.current_user()
    group_id = vars.file.info.group_id
    comment("start handling uploaded file")
    user_id = int(vars.user_id) if vars.user_id else auth.current_user()
    fil = vars.file
    result = save_uploaded_photo(fil.name, fil.BINvalue, user_id)
    duplicate = False
    if result.duplicate:
        photo_id = result.duplicate
        duplicate = True
    else:
        photo_id = result.photo_id
    photo_rec = db(db.TblPhotos.id == photo_id).select().first()
    group_rec = db(db.TblGroups.id==group_id).select().first()
    topic_id=group_rec.topic_id
    topic_rec = db(db.TblTopics.id==topic_id).select().first()
    if not duplicate:
        new_id = db.TblItemTopics.insert(
            item_type="P",
            topic_id=topic_id,
            story_id=photo_rec.story_id)
        if 'P' not in topic_rec.usage:
            usage = topic_rec.usage + 'P'
            topic_rec.update_record(usage=usage, topic_kind=2) #simple topic
    photo_url=timestamped_photo_path(photo_rec)
    photo_width = photo_rec.width
    photo_height = photo_rec.height
    if duplicate:
        story_rec = db(db.TblStories.id==photo_rec.story_id).select().first()
        photo_name = story_rec.name
        photo_story = story_rec.story.replace('\n', '').replace('<p>', '').replace('</p>', '\n')
        all_dates = get_all_dates(photo_rec)
        photographer = db(db.TblPhotographers.id==photo_rec.photographer_id).select().first()
        photographer_id = photo_rec.photographer_id or 0
        photographer_name = photographer.name if photographer else ''
        photo_date_str = all_dates.photo_date.date
        photo_date_datespan = all_dates.photo_date.span
        longitude = photo_rec.longitude
        latitude = photo_rec.latitude
        zoom = photo_rec.zoom
    else:
        photo_name = fil.name
        photo_story = ''
        photographer_id = 0
        photographer_name = ''
        photo_date_str = ''
        photo_date_datespan = 0
        longitude = None
        latitude = None
        zoom = 8
    photo_topics = get_photo_topics(photo_rec.story_id)
    topic_names = [topic['name'] for topic in photo_topics]
    keywords = ';'.join(topic_names)
    db(db.TblStories.id==photo_rec.story_id).update(keywords=keywords)
    
    ws_messaging.send_message(key='GROUP-PHOTO-UPLOADED', group=vars.file.info.ptp_key, photo_url=photo_url, photo_name=photo_name, 
                              photo_id=photo_id, photo_story=photo_story, duplicate=duplicate,
                              photographer_name=photographer_name,photo_date_str=photo_date_str,photo_date_datespan=photo_date_datespan,
                              longitude=longitude,latitude=latitude,zoom=zoom, photo_topics=photo_topics, 
                              photographer_id=photographer_id, photo_width=photo_width, photo_height=photo_height)
    return dict(photo_url=photo_url, upload_result=dict(duplicate=duplicate))

@serve_json
def attempt_login(vars):
    user_id = 0;
    user = auth.login_bare(vars.email, "", sneak_in=True)
    if isinstance(user, str):
        return dict(warning_message=user)
    if user:
        user_id = user.id
    return dict(user_id=user_id)

@serve_json
def register_user(vars):
    user_id = access_manager.register_new_user(vars.email, vars.password, vars.first_name, vars.last_name, registration_key='')
    am = access_manager.AccessManager()
    grp_ids = [RESTRICTED, PHOTO_UPLOADER, EDITOR]
    am.enable_roles(user_id, grp_ids)
    return dict(user_id=user_id)

@serve_json
def save_photo_info(vars):
    photo_id = int(vars.photo_id)
    photo_rec = db(db.TblPhotos.id==photo_id).select().first()
    sm = stories_manager.Stories()
    sm.update_story(
        photo_rec.story_id, 
        Storage(
            story_text=text_to_html(vars.photo_info.photo_story),
            name=vars.photo_info.photo_name,
            used_for=STORY4PHOTO
        )
    )
    photo_date_str = vars.photo_info.photo_date_str
    photo_date_datespan = vars.photo_info.photo_date_datespan
    photo_dates_info = dict(
        photo_date = (photo_date_str, int(photo_date_datespan))
    )
    rec = db(db.TblPhotos.id==photo_id).select().first()
    update_record_dates(rec, photo_dates_info)
    photographer_name = vars.photo_info.photographer_name
    prec = db(db.TblPhotographers.name == photographer_name).select().first()
    if prec:
        rec.update_record(photographer_id=prec.id)
    else:
        pid = db.TblPhotographers.insert(name=photographer_name, kind='P')
    return dict()

@serve_json
def mail_contacts(vars):
    group_id = vars.group_id
    from_name = vars.from_name or 'Test'
    comment("enter mail contacts, from: {}, group {}", from_name, group_id)
    recipients = db((db.TblGroupContacts.group_id==group_id) & (db.TblGroupContacts.deleted != True)).select()
    receivers = [gc.email for gc in recipients]
    grec = db(db.TblGroups.id==group_id).select().first()
    db(db.TblTopics.id==grec.topic_id).select().first().name
    host = request.env.http_host
    #build recipient list and pass to send_mail
    sender=f"info@{host}"
    subject=grec.description
    message=vars.mail_body
    if vars.personal:
        send_personal_email(recipients, sender, subject, message=message)
    else:
        result = email(receivers=receivers, sender=sender, subject=grec.description, message=vars.mail_body)
    return dict(result = result)

#-----------support functions----------------------------

def send_personal_email(recipients, sender, subject, message):
    result = True
    for recipient in recipients:
        message = fill_data(message, recipient)
        result = result and email(receivers=[recipient.email], sender=sender, subject=subject, message=message)
    return result

def fill_data(message, recipient):
    def subst(match):
        symbol = match.group(1)
        return recipient[symbol]
    return re.sub(r"!\[#([^#]+)#\]", lambda match: subst(match), message)

def text_to_html(txt):
    lst = txt.split('\n')
    lst = ['<p>' + seg + '</p>' for seg in lst]
    return ''.join(lst)

MAX_SIZE = 256

def get_logo_url(group_id):
    group_id = int(group_id)
    rec = db(db.TblGroups.id==group_id).select().first()
    folder = url_folder('logos')
    logo_name = rec.logo_name if rec and rec.logo_name else 'dummy-logo.png'
    return folder + logo_name

def save_uploaded_logo(file_name, binVal, group_id):
    img, crc = str_to_image(binVal)
    original_file_name, ext = os.path.splitext(file_name)
    crc &= 0xffffffff
    file_name = f'{crc:x}{ext}'
    path = local_folder('logos')
    dir_util.mkpath(path)
    width, height = img.size
    
    if height > MAX_SIZE or width > MAX_SIZE:
        width, height = resized(width, height)
        img = img.resize((width, height), Image.LANCZOS)
    img.save(path + file_name)
    db(db.TblGroups.id==group_id).update(logo_name=file_name)
    ws_messaging.send_message(key='GROUP-LOGO-UPLOADED', group='ALL', group_id=group_id, logo_url=get_logo_url(group_id))
    return file_name

def resized(width, height):
    x = 1.0 * MAX_SIZE / width
    y = 1.0 * MAX_SIZE / height
    r = x if x < y else y
    return int(round(r * width)), int(round(r * height))
