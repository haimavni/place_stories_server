import stories_manager
import csv, cStringIO
from porting.create_old_db_mappings import get_records

@serve_json
def get_help(vars):
    topic = vars.topic
    sm = stories_manager.Stories()
    story_info = sm.find_story(STORY4HELP, topic)
    if not story_info:
        story_info = Storage(display_version='New Story',
                             name="help for " + topic,
                             topic=topic,
                             story_versions=[], 
                             story_text='help.not-ready', 
                             story_id=None,
                             used_for = STORY4HELP
                             )
    return dict(story_info=story_info)

@serve_json
def save_help(vars):
    #this code is currently not called! the story is saved like any other story!
    story_info = vars.story_info
    topic = story_info.topic
    rec = db((db.TblStories.used_for==STORY4HELP) & (db.TblStories.topic==topic)).select().first()
    if rec:
        story_id = rec.id
        if story_id != story_info.story_id:
            x = 999 #bug? breakpoint here
    else:
        story_id = None
    sm = stories_manager.Stories()
    if not story_id:
        result = sm.add_story(story_info)
        story_id = result.story_id
    else:
        sm.update_story(story_id, story_info)
    save_help_messages_to_csv()
        
def default_csv_name():
    return 'applications/{}/private/help_messages.csv'.format(request.application)

@serve_json
def save_help_messages_to_csv(vars):
    csv_name = vars.cvs_name or default_csv_name();
    rows = db(db.TblStories.used_for==STORY4HELP).select(db.TblStories.name, db.TblStories.topic, db.TblStories.story)
    with open(csv_name, 'w') as f:
        rows.export_to_csv_file(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)

@serve_json
def load_help_messages_from_csv(vars):
    csv_name = vars.cvs_name or default_csv_name();
    for rec in get_records(csv_name):
        pass
        ##db(db.TblStories.id==rec.id).update(**rec)
        
