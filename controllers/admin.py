from admin_support.access_manager import AccessManager
from admin_support.task_monitor import TaskMonitor
import ws_messaging
import os
import re
from photos_support import get_padded_photo_url

#---------------------------------------------------------------------------
# Access Manager
#---------------------------------------------------------------------------

###@auth.requires_login()  #todo: fix it sometime... maybe
def access_manager():
    return dict()

@serve_json
def get_authorized_users(vars):
    am = AccessManager()
    return dict(authorized_users=am.get_users_data())

@serve_json
def toggle_membership(vars):
    am = AccessManager()
    role_name = vars.role
    role = eval(role_name)
    active = vars.active != 'true'
    am.modify_membership(vars.id, role, active)
    ws_messaging.send_message(key='ROLE_CHANGED', group='ALL', user_id=vars.id, role=role_name, active=active) 
    return dict(id=vars.id, 
                role=vars.role, 
                active=active)

@serve_json
def add_or_update_user(vars):
    am = AccessManager()
    vars.confirm_password = vars.password #avoid passwords dont match error
    user_data, is_new_user = am.add_or_update_user(vars)
    return dict(user_data=user_data, 
                new_user=is_new_user)

@serve_json
def delete_user(vars):
    uid = vars.id
    n = db(db.auth_user.id==uid).delete()
    return dict(id=vars.id, ok=n==1)

#---------------------------------------------------------------------------
# Task Monitor
#---------------------------------------------------------------------------

@auth.requires_login()
def task_monitor():
    return dict(controller='TaskMonitorCtrl')

@serve_json
def read_tasks(vars):
    tm = TaskMonitor()
    logging.disable(logging.DEBUG)
    task_list=tm.all_tasks()
    logging.disable(logging.NOTSET)
    return dict(task_list=tm.all_tasks())

@serve_json
def restart_task(vars):
    tm = TaskMonitor()
    tm.restart_task(vars.task_id)
    return dict()

@serve_json
def stop_task(vars):
    tm = TaskMonitor()
    tm.stop_task(vars.task_id)
    return dict()

@serve_json
def delete_task(vars):
    tm = TaskMonitor()
    tm.delete_task(vars.task_id)
    return dict()

@serve_json
def remove_completed_tasks(vars):
    tm = TaskMonitor()
    tm.remove_completed_tasks()
    return dict()

@serve_json
def resend_verification_email(vars):
    auth.resend_verification_email(vars.user_id)
    return dict()

@serve_json
def unlock_user(vars):
    am = AccessManager()
    am.unlock_user(vars.user_id)
    return dict()
    
@serve_json
def reindex_words(vars):
    db(db.TblStories.deleted != True).update(indexing_date = NO_DATE)
    return dict()

@serve_json
def set_user_registration_options(vars):
    config_rec = db(db.TblConfiguration).select().first()
    if not config_rec:
        db.TblConfiguration.insert()
        config_rec = db(db.TblConfiguration).select().first()
    enable_auto_reg = vars.option == 'user.auto-reg'
    config_rec.update_record(enable_auto_registration=enable_auto_reg)
    return dict()

@serve_json
def set_new_app_options(vars):
    config_rec = db(db.TblConfiguration).select().first()
    if not config_rec:
        db.TblConfiguration.insert()
        config_rec = db(db.TblConfiguration).select().first()
    expose_new_app_button = vars.option == 'user.new-app-enabled'
    config_rec.update_record(expose_new_app_button=expose_new_app_button)
    return dict()

@serve_json
def set_audio_option(vars):
    config_rec = db(db.TblConfiguration).select().first()
    if not config_rec:
        db.TblConfiguration.insert()
        config_rec = db(db.TblConfiguration).select().first()
    support_audio = vars.option == 'user.audio-enabled'
    config_rec.update_record(support_audio=support_audio)
    return dict()

@serve_json
def set_feedback_option(vars):
    config_rec = db(db.TblConfiguration).select().first()
    if not config_rec:
        db.TblConfiguration.insert()
        config_rec = db(db.TblConfiguration).select().first()
    feedback_on = vars.option == 'user.feedback-on'
    config_rec.update_record(expose_feedback_button=feedback_on)
    return dict()

@serve_json
def set_exclusive_option(vars):
    config_rec = db(db.TblConfiguration).select().first()
    if not config_rec:
        db.TblConfiguration.insert()
        config_rec = db(db.TblConfiguration).select().first()
    exclusive_on = vars.option == 'user.exclusive-on'
    config_rec.update_record(exclusive=exclusive_on)
    return dict()

@serve_json
def set_version_time_option(vars):
    config_rec = db(db.TblConfiguration).select().first()
    if not config_rec:
        db.TblConfiguration.insert()
        config_rec = db(db.TblConfiguration).select().first()
    version_time_on = vars.option == 'user.version-time-on'
    config_rec.update_record(expose_version_time=version_time_on)
    return dict()

@serve_json
def set_developer_option(vars):
    config_rec = db(db.TblConfiguration).select().first()
    if not config_rec:
        db.TblConfiguration.insert()
        config_rec = db(db.TblConfiguration).select().first()
    developer_on = vars.option == 'user.expose-developer-on'
    config_rec.update_record(expose_developer=developer_on)
    return dict()

@serve_json
def set_articles_option(vars):
    config_rec = db(db.TblConfiguration).select().first()
    if not config_rec:
        db.TblConfiguration.insert()
        config_rec = db(db.TblConfiguration).select().first()
    articles_on = vars.option == 'user.enable-articles-on'
    config_rec.update_record(enable_articles=articles_on)
    return dict()

@serve_json
def set_books_option(vars):
    config_rec = db(db.TblConfiguration).select().first()
    if not config_rec:
        db.TblConfiguration.insert()
        config_rec = db(db.TblConfiguration).select().first()
    books_on = vars.option == 'user.enable-books-on'
    config_rec.update_record(enable_books=books_on)
    return dict()

@serve_json
def set_member_of_the_day_option(vars):
    config_rec = db(db.TblConfiguration).select().first()
    if not config_rec:
        db.TblConfiguration.insert()
        config_rec = db(db.TblConfiguration).select().first()
    member_of_the_day_on = vars.option == 'user.enable-member-of-the-day-on'
    config_rec.update_record(enable_member_of_the_day=member_of_the_day_on)
    return dict()

@serve_json
def set_cuepoints_option(vars):
    config_rec = db(db.TblConfiguration).select().first()
    if not config_rec:
        db.TblConfiguration.insert()
        config_rec = db(db.TblConfiguration).select().first()
    cuepoints_on = vars.option == 'user.enable-cuepoints-on'
    config_rec.update_record(enable_cuepoints=cuepoints_on)
    return dict()

@serve_json
def set_publishing_option(vars):
    config_rec = db(db.TblConfiguration).select().first()
    if not config_rec:
        db.TblConfiguration.insert()
        config_rec = db(db.TblConfiguration).select().first()
    allow_publishing_on = vars.option == 'user.allow-publishing-on'
    config_rec.update_record(allow_publishing=allow_publishing_on)
    return dict()

@serve_json
def set_expose_gallery_option(vars):
    config_rec = db(db.TblConfiguration).select().first()
    if not config_rec:
        db.TblConfiguration.insert()
        config_rec = db(db.TblConfiguration).select().first()
    expose_gallery_on = vars.option == 'user.expose-gallery-on'
    config_rec.update_record(expose_gallery=expose_gallery_on)
    return dict()

@serve_json
def set_quick_upload_option(vars):
    config_rec = get_config_rec()
    quick_upload_on = vars.option == 'user.quick-upload-on'
    config_rec.update_record(quick_upload_button=quick_upload_on)
    return dict()

@serve_json
def set_promoted_story_expiration(vars):
    config_rec = get_config_rec()
    config_rec.update_record(promoted_story_expiration=int(vars.promoted_story_expiration))
    return dict()

@serve_json
def cover_photo(vars):
    cover_photo = get_padded_photo_url(vars.cover_photo_id)
    config_rec = get_config_rec()
    if cover_photo is not None:
        config_rec.update_record(cover_photo=cover_photo, cover_photo_id=vars.cover_photo_id)
    return dict(cover_photo=cover_photo)


def get_config_rec():
    config_rec = db(db.TblConfiguration).select().first()
    if not config_rec:
        db.TblConfiguration.insert()
        config_rec = db(db.TblConfiguration).select().first()
    return config_rec
    
def reindex_stories():
    from words import update_word_index_all
    update_word_index_all()

def create_app_index():
    app = request.application
    path = 'applications/{app}/static/aurelia/'.format(app=app)
    src = path + 'index.html'
    dst = path + f'index-{request.application}.html'
    if os.path.isfile(dst):
        return f'{dst} already exists'
    with open(src, 'r', encoding='utf-8') as f:
        s = f.read()
    pat = r'<title>.*?</title>'
    s1 = re.sub(pat, replace_title, s)
    if not app.startswith("gbs__"):
        s1 = s1.replace('gbstories.org', 'tol.life')
    with open(dst, 'w', encoding='utf-8') as f:
        f.write(s1)
    return '{} was created'.format(dst)

def replace_title(m):
    rec = db((db.TblLocaleCustomizations.lang=='he') & (db.TblLocaleCustomizations.key=='app-title')).select().first()
    if rec:
        return '<title>' + rec.value + '</title>'
    else:
        return m.group(0)
