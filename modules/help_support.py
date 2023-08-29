from . import stories_manager
import csv, io
from .folders import local_folder, system_folder
import re
from .injections import inject
import os, datetime
from gluon.storage import Storage

def save_help(name, topic, content, imported_from=''):
    STORY4HELP = inject('STORY4HELP')
    return _save_system_story(name, topic, content, imported_from=imported_from, used_for=STORY4HELP)

def save_letter(name, topic, content, imported_from=''):
    STORY4LETTER = inject('STORY4LETTER')
    return _save_system_story(name, topic, content, imported_from=imported_from, used_for=STORY4LETTER)

def save_help_messages_to_csv(target=None):
    STORY4HELP = inject('STORY4HELP')
    return _save_system_stories_to_csv(target=target, used_for=STORY4HELP)

def save_letter_templates_to_csv(target=None):
    STORY4LETTER = inject('STORY4LETTER')
    return _save_system_stories_to_csv(target=target, used_for=STORY4LETTER)

def load_help_messages_from_csv():
    STORY4HELP = inject('STORY4HELP')
    return _load_system_stories_from_csv(used_for=STORY4HELP)

def load_letter_templates_from_csv():
    STORY4LETTER = inject('STORY4LETTER')
    return _load_system_stories_from_csv(used_for=STORY4LETTER)

def update_help_messages():
    STORY4HELP = inject('STORY4HELP')
    return _update_system_stories(used_for=STORY4HELP)

def update_letter_templates():
    STORY4LETTER = inject('STORY4LETTER')
    return _update_system_stories(used_for=STORY4LETTER)

def get_overridden_help_messages():
    STORY4HELP = inject('STORY4HELP')
    return _get_overridden_system_stories(STORY4HELP)

def get_overridden_letter_templates():
    STORY4LETTER = inject('STORY4LETTER')
    return _get_overridden_system_stories(STORY4LETTER)

#--------------------------------------------------------------------------------------------

def _system_stories_file_name(used_for):
    STORY4HELP, STORY4LETTER = inject('STORY4HELP', 'STORY4LETTER')
    if used_for == STORY4HELP:
        return 'help_messages'
    if used_for == STORY4LETTER:
        return 'letter_templates'
    raise Exception('Unknown system story type')

def _save_system_story(name, topic, content, imported_from='', used_for=None, last_update=None):
    db = inject('db')
    rec = db((db.TblStories.used_for==used_for) & (db.TblStories.topic==topic)).select().first()
    if rec:
        last_update = datetime.datetime.strptime(last_update, '%Y-%m-%d %H:%M:%S')
        if last_update and last_update <= rec.last_update_date:
            return
        story_id = rec.id
    else:
        story_id = None
    story_info = Storage(
        name=name,
        topic=topic,
        story_text=content,
        story_id=story_id,
        used_for = used_for
    )
    sm = stories_manager.Stories()
    if story_id:
        sm.update_story(story_id, story_info, imported_from=imported_from)
    else:
        sm.add_story(story_info, imported_from=imported_from)

def _save_system_stories_to_csv(target=None, used_for=None):
    filename = _system_stories_file_name(used_for)
    db = inject('db')
    folder = system_folder() if target == 'system' else local_folder('help')
    csv_name = folder + filename + '.csv'
    rows = db(db.TblStories.used_for==used_for).select(db.TblStories.name, db.TblStories.topic, db.TblStories.story, db.TblStories.last_update_date)
    with open(csv_name, 'w') as f:
        rows.export_to_csv_file(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
    return dict(good=True)

def get_records(csv_name):
    with open(csv_name, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        next(reader)     #skip header
        for row in reader:
            yield row

def _update_system_stories(used_for=None):
    db, NO_TIME, comment, log_exception = inject('db', 'NO_TIME', 'comment', 'log_exception')
    ###comment(f"Enter updating system stories {used_for}")
    try:
        filename = system_folder() + _system_stories_file_name(used_for) + '.csv'
        if not os.path.exists(filename):
            comment(f"{filename} not found ")
            return "No source for update"
        ctime = round(os.path.getctime(filename))
        dt = datetime.datetime.fromtimestamp(ctime)
        crec = db(db.TblConfiguration).select().first()
        field_name = _system_stories_file_name(used_for) + '_upload_time'
        last_update = crec[field_name] or NO_TIME
        if dt > last_update: #need to update
            comment(f"Updating system stories {used_for}")
            _load_system_stories_from_csv(used_for)
            data = {field_name: dt}
            crec.update_record(**data)
            return 'updated'
        ###comment(f"Exit updating system stories {used_for}")
    except Exception as e:
        log_exception("Update system stories failed")
    return 'No updates'

def _load_system_stories_from_csv(used_for=None):
    filename = _system_stories_file_name(used_for)
    db = inject('db')
    csv_name = system_folder() + filename + '.csv'
    imported_from = 'system'
    for rec in get_records(csv_name):
        if len(rec) == 3:
            rec += ['0001-01-01 0:0:0']
        name, topic, content, last_update = rec
        _save_system_story(name, topic, content, imported_from=imported_from, used_for=used_for, last_update=last_update)
    db.commit()
    return

def _get_overridden_system_stories(used_for):
    db = inject('db')
    q = (db.TblStories.used_for==used_for) & (db.TblStories.imported_from=='SYSTEM') & (db.TblStories.last_version > 0)
    lst = db(q).select(db.TblStories.id, db.TblStories.topic, db.TblStories.name, db.TblStories.last_version, orderby=db.TblStories.name)
    return lst

