import stories_manager
import csv, cStringIO
from folders import local_folder

@serve_json
def get_letter(vars):
    topic = vars.topic
    sm = stories_manager.Stories()
    story_info = sm.find_story(STORY4LETTER, topic)
    if not story_info:
        story_info = Storage(display_version='New Story',
                             name="letter for " + topic,
                             topic=topic,
                             story_versions=[], 
                             story_text='letter.not-ready', 
                             story_id=None,
                             used_for = STORY4LETTER
                             )
    return dict(story_info=story_info)

def save_letter(name, topic, content):
    rec = db((db.TblStories.used_for==STORY4LETTER) & (db.TblStories.topic==topic)).select().first()
    if rec:
        story_id = rec.id
    else:
        story_id = None
    story_info = Storage(
        name=name,
        topic=topic,
        story_text=content,
        story_id=story_id,
        used_for = STORY4LETTER
    )
    sm = stories_manager.Stories()
    if story_id:
        sm.update_story(story_id, story_info)
    else:
        sm.add_story(story_info)

def default_csv_name():
    return local_folder('letters') + 'letters.csv'

@serve_json
def save_letters_to_csv(vars):
    csv_name = vars.cvs_name or default_csv_name();
    rows = db(db.TblStories.used_for==STORY4LETTER).select(db.TblStories.name, db.TblStories.topic, db.TblStories.story)
    with open(csv_name, 'w') as f:
        rows.export_to_csv_file(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
    return dict(good=True)

@serve_json
def load_letters_from_csv(vars):
    csv_name = vars.cvs_name or default_csv_name();
    for rec in get_records(csv_name):
        name, topic, content = rec
        save_letter(name, topic, content)
    db.commit()
    return dict(good=True)

def get_records(csv_name):
    with open(csv_name, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        reader.next()     #skip header
        for row in reader:
            yield row


