import stories_manager
import csv, cStringIO
from folders import local_folder, system_folder
import re
import help_support

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
def save_help_messages_to_csv(vars):
    return help_support.save_help_messages_to_csv(target=vars.target)

@serve_json
def load_help_messages_from_csv(vars):
    return help_support.load_help_messages_from_csv()

@serve_json
def print_all_messages(vars):
    file_name = vars.file_name or 'help_messages'
    fname = '{p}{n}[{a}].hlp'.format(p=log_path(), n=file_name, a=request.application)
    with open(fname, 'w') as f:
        lst = db(db.TblStories.used_for==STORY4HELP).select(db.TblStories.id, db.TblStories.name, db.TblStories.topic, db.TblStories.story, orderby=db.TblStories.topic)
        for hrec in lst:
            f.write('{t}: {n}\n'.format(t=hrec.topic, n=hrec.name))
            f.write('-----------------------------------------------------------\n')
            s = break_to_lines(hrec.story)
            f.write(s)
            f.write('\n')
    return dict()

@serve_json
def get_help_message(vars):
    story_id = int(vars.story_id)
    sm = stories_manager.Stories()
    story_info = sm.get_story(story_id)
    prev_story_info = sm.get_story(story_id, to_story_version=-1)
    return dict(story_info=story_info, prev_story_info=prev_story_info)

@serve_json
def get_overridden_help_messages(vars):
    return dict(message_list=help_support.get_overridden_help_messages())

def break_to_lines(s):
    s = re.sub(r'^\s+', '', s)
    s = s.replace('\n', '')
    s = break_string(s)
    s = s.replace('>', '>\n')
    return s

def break_string(s, max_len=80):
    lst = s.split()
    result = ''
    line = ''
    for t in lst:
        u = line.decode('utf8')
        if len(u) >= max_len:
            result += '\n' + line
            line = t
        else:
            line += ' ' + t
    result += '\n' + line
    return result
        


