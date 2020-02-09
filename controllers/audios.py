from audios_support import save_uploaded_audio, audio_url
from members_support import calc_grouped_selected_options, calc_all_tags, get_tag_ids
from gluon.storage import Storage
from date_utils import date_of_date_str, parse_date, get_all_dates, update_record_dates, fix_record_dates_in, fix_record_dates_out
import stories_manager

@serve_json
def get_audio_list(vars):
    audio_list = db(db.TblAudios).select()
    
    for rec in audio_list:
        fix_record_dates_out(rec)
        story = get_story_by_id(rec.story_id)
        rec.story = story
        rec.audio_path=audio_url(rec.story_id)
    return dict(audio_list=audio_list, no_results=not audio_list)

@serve_json
def upload_audio(vars):
    comment("start handling uploaded audio file")
    user_id = int(vars.user_id) if vars.user_id else auth.current_user()
    fil = vars.file
    result = save_uploaded_audio(fil.name, fil.BINvalue, user_id)
    return dict(upload_result=result)

@serve_json
def apply_to_checked_audios(vars):
    all_tags = calc_all_tags()
    params = vars.params
    adl = params.checked_audio_list
    if params.audios_date_str:
        dates_info = dict(
            audio_date = (params.audios_date_str, params.audios_date_span_size)
        )
    else:
        dates_info = None

    st = params.selected_topics
    added = []
    deleted = []
    changes = dict()
    new_topic_was_added = False
    for story_id in adl:
        drec = db(db.TblAudios.story_id==story_id).select().first()
        curr_tag_ids = set(get_tag_ids(drec.id, 'A'))
        for tpc in st:
            topic = tpc.option
            ###item = dict(item_id=audio_id, topic_id=topic.id)
            audio_id = drec.id
            if topic.sign=="plus" and topic.id not in curr_tag_ids:
                new_id = db.TblItemTopics.insert(item_type='D', item_id=audio_id, topic_id=topic.id, story_id=story_id) 
                curr_tag_ids |= set([topic.id])
                ###added.append(item)
                topic_rec = db(db.TblTopics.id==topic.id).select().first()
                if topic_rec.topic_kind == 0: #never used
                    new_topic_was_added = True
                if 'A' not in topic_rec.usage:
                    usage = topic_rec.usage + 'A'
                    topic_rec.update_record(usage=usage, topic_kind=2) #topic is simple 
            elif topic.sign=="minus" and topic.id in curr_tag_ids:
                q = (db.TblItemTopics.item_type=='A') & (db.TblItemTopics.item_id==audio_id) & (db.TblItemTopics.topic_id==topic.id)
                curr_tag_ids -= set([topic.id])
                ###deleted.append(item)
                db(q).delete()
        curr_tags = [all_tags[tag_id] for tag_id in curr_tag_ids]
        keywords = "; ".join(curr_tags)
        changes[audio_id] = dict(keywords=keywords, audio_id=audio_id)
        rec = db(db.TblAudios.id==audio_id).select().first()
        rec.update_record(keywords=keywords)  #todo: remove this line soon
        rec = db(db.TblStories.id==rec.story_id).select().first()
        rec.update_record(keywords=keywords)
        if dates_info:
            update_record_dates(rec, dates_info)
    ###changes = [changes[audio_id] for audio_id in adl]
    ###ws_messaging.send_message('audio-TAGS-CHANGED', group='ALL', changes=changes)
    return dict(new_topic_was_added=new_topic_was_added)


def get_story_by_id(story_id):
    sm = stories_manager.Stories()
    return sm.get_story(story_id)


