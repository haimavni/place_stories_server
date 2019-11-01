import csv, cStringIO
from folders import local_folder
import stories_manager

def init_database():
    password = request.vars.password
    email = request.vars.email
    #load help messages
    load_help_messages_from_csv()
    #these values are passed from the hub application. if they exist, create the owner account with all privileges
    return "database initialized"

###help messages support. duplicate of help.py

def load_help_messages_from_csv():
    csv_name = default_csv_name();
    for rec in get_records(csv_name):
        name, topic, content = rec
        save_help(name, topic, content)

def get_records(csv_name):
    with open(csv_name, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        reader.next()     #skip header
        for row in reader:
            yield row

def save_help(name, topic, content):
    rec = db((db.TblStories.used_for==STORY4HELP) & (db.TblStories.topic==topic)).select().first()
    if rec:
        story_id = rec.id
    else:
        story_id = None
    story_info = Storage(
        name=name,
        topic=topic,
        story_text=content,
        story_id=story_id,
        used_for = STORY4HELP
    )
    sm = stories_manager.Stories()
    if story_id:
        sm.update_story(story_id, story_info)
    else:
        sm.add_story(story_info)

def default_csv_name():
    return local_folder('help') + 'help_messages.csv'



