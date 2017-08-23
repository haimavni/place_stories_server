import stories_manager

@serve_json
def get_help(vars):
    topic = vars.topic
    rec = db(db.TblHelp.topic==topic).select().first()
    if rec:
        story_id = rec.story_id
        sm = stories_manager.Stories()
        story_info = sm.get_story(member_info.story_id)
    else:
        story_info = Storage(display_version='New Story',
                             name="help for " + topic,
                             story_versions=[], 
                             story_text='help.not-ready', 
                             story_id=None,
                             used_for = STORY4MEMBER
                             )
    return dict(
        title = story_info.name,
        content = story_info.story_text
    )

@serve_json
def save_help(vars):
    topic = vars.topic
    story_id = vars.story_id
    story_info = Storage(
        name=vars.name,
        story_text=vars.content,
        used_for = STORY4MEMBER
    )
    sm = stories_manager.Stories()
    if not story_id:
        result = sm.add_story(story_info)
        story_id = result.story_id
        dbTblHelp.insert(topic=topic, story_id=story_id)
    else:
        sm.update_story(story_id, story_info)
