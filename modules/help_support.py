import stories_manager
import csv, cStringIO
from folders import local_folder, system_folder
import re
from injections import inject
import os, datetime

def default_csv_name():
    return local_folder('help') + 'help_messages.csv'

def save_system_story(name, topic, content, imported_from='', used_for=None):
    db = inject('db')
    rec = db((db.TblStories.used_for==used_for) & (db.TblStories.topic==topic)).select().first()
    if rec:
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

def save_help(name, topic, content, imported_from=''):
    STORY4HELP = inject('STORY4HELP')
    return save_system_story(name, topic, content, imported_from=imported_from, used_for=STORY4HELP)

def save_system_stories_to_csv(target=None, used_for=None, filename=None):
    db = inject('db')
    folder = system_folder() if target == system else local_folder('help')
    csv_name = folder + filename + '.csv'
    rows = db(db.TblStories.used_for==used_for).select(db.TblStories.name, db.TblStories.topic, db.TblStories.story)
    with open(csv_name, 'w') as f:
        rows.export_to_csv_file(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
    return dict(good=True)

def save_help_messages_to_csv(target=None):
    STORY4HELP = inject('STORY4HELP')
    return save_system_stories_to_csv(target=target, 
                                      used_for=STORY4HELP, 
                                     filename='help_messages')

def load_system_stories_from_csv(filename, used_for=None):
    db = inject('db')
    csv_name = system_folder() + filename + '.csv'
    imported_from = 'system'
    for rec in get_records(csv_name):
        name, topic, content = rec
        save_system_story(name, topic, content, imported_from=imported_from, used_for=used_for)
    db.commit()
    return

def load_help_messages_from_csv():
    STORY4HELP = inject('STORY4HELP')
    return load_system_stories_from_csv('help_messages', used_for=STORY4HELP)

def get_records(csv_name):
    with open(csv_name, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        reader.next()     #skip header
        for row in reader:
            yield row

def update_help_messages():
    db, NO_DATE = inject('db', 'NO_DATE')
    fname = system_folder() + 'help_messages.csv'
    ctime = os.path.getctime(fname)
    dt = datetime.datetime.fromtimestamp(ctime)
    crec = db(db.TblConfiguration).select().first()
    last_help_update = crec.last_help_update or NO_DATE
    if dt > last_help_update: #need to update
        load_help_messages_from_csv()

