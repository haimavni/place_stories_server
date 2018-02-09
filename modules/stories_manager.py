import merge_in_memory as mim
import datetime
from injections import inject
from gluon.storage import Storage
from words import *

def display_date(dt):
    return str(dt)[:19]

def get_display_version(num, sv):
    return '#{num} {dt} by {email}'.format(num=num, dt=display_date(sv.creation_time), email=sv.email)
    

class Stories:
    
    def __init__(self, author_id=None, language=None):
        if not author_id:
            auth = inject('auth')
            author_id = auth.current_user()
        self.author_id = author_id
        self.language = language

    def get_story(self, story_id, from_story_version=None, to_story_version=None):
        db = inject('db')
        rec = db(db.TblStories.id==story_id).select().first()
        if not rec:
            return None
        if self.language:  
            if rec.language != self.language:
                rec1 = self.find_translation(story_id, language)
                if rec1:
                    rec = rec1
                # else we have to read in the original language
        rec = Storage(rec)
        story = rec.story
        q = (db.TblStoryVersions.story_id==story_id)
        story_versions = db(q).select(db.TblStoryVersions.story_id, db.TblStoryVersions.creation_date, db.TblStoryVersions.author_id)
        story_versions = [Storage(sv) for sv in story_versions]
        current_version = len(story_versions)
        display_version = 'The original Story'
        for i, sv in enumerate(story_versions):
            if not sv:
                continue
            tmp = db(db.auth_user.id==sv.author_id).select(db.auth_user.email).first()
            sv.email = tmp.email if tmp else ''
            sv.display_version = get_display_version(i, sv)
        if to_story_version is None:
            story_text = story
            to_story = current_version
        else:
            from_story_version = from_story_version or current_version
            reverse = to_story_version < from_story_version
            if reverse:
                dif_recs = story_versions[to_story_version:from_story_version]
            else:
                dif_recs = story_versions[from_story_version:to_story_version]
            diffs = [r.delta for r in dif_recs]
            merger = mim.Merger()
            story_text = merger.diff_apply_bulk(story, diffs, reverse=reverse)
            display_version = story_versions[to_story_version].display_version
        story_info = Storage(
            story_text=story_text,
            story_preview=get_reisha(story_text),
            name=rec.name,
            topic=rec.topic,
            story_id=story_id,   #we always access via the master
            source=rec.source,
            used_for=rec.used_for,
            author_id=rec.author_id,
            language=rec.language,
            story_curr_version=to_story_version,
            story_versions=story_versions,
            display_version=display_version
        )
        return story_info
    
    def get_empty_story(self, used_for=2):
        story_info = Storage(
            story_text="New Story",
            story_preview=[],
            name='stories.new-story',
            topic="",
            story_id="new",   #we always access via the master
            source="",
            used_for=used_for,
            author_id=None
            )
        return story_info

    def add_story(self, story_info, story_id=None, language=None, owner_id=None):
        story_text = story_info.story_text
        if not language: #we just found it before we called = no need to recalculate
            language = guess_language(story_text)
        name = story_info.name
        story_text = story_text.replace('~1', '&').replace('~2', ';').replace('\n', '').replace('>', '>\n')
        now = datetime.datetime.now()
        db, auth, STORY4EVENT, STORY4TERM = inject('db', 'auth', 'STORY4EVENT', 'STORY4TERM')
        author_name = auth.user_name(self.author_id)
        ###todo: handle language issues here and in update_story
        story_id = db.TblStories.insert(story=story_text, 
                                        author_id=self.author_id, 
                                        name=name,
                                        source=author_name,
                                        used_for=story_info.used_for,
                                        translated_from=story_id,
                                        creation_date=now,
                                        language=language,
                                        topic=story_info.topic,
                                        last_update_date=now)
        if story_info.used_for == STORY4EVENT:
            db.TblEvents.insert(
                story_id=story_id,
                ###event_date=
                ###event_date_str=
            )
        elif story_info.used_for == STORY4TERM:    
            db.TblTerms.insert(
                story_id=story_id,
                ###event_date=
                ###event_date_str=
            )
        
        update_story_words_index(story_id)
        return Storage(story_id=story_id, creation_date=now, author=author_name)

    def update_story(self, story_id, story_info, language=None):
        if story_id == 'new':
            return self.add_story(story_info)
        updated_story_text = story_info.story_text
        if language:
            rec1 = self.find_translation(story_id, language)
            if rec1:
                return self.update_story(story_id, story_info)
            else:
                return self.add_story(story_info, story_id)
        else:
            language = guess_language(updated_story_text)
        updated_story_text = updated_story_text.replace('~1', '&').replace('~2', ';').replace('\n', '').replace('>', '>\n')
        db, auth = inject('db', 'auth')
        rec = db(db.TblStories.id==story_id).select().first()
        #if rec.language and rec.language != language:
            #rec = self.find_translation(rec, language)
        now = datetime.datetime.now()
        if rec.story != updated_story_text:
            merger = mim.Merger()
            delta = merger.diff_make(rec.story, updated_story_text)
            rec.update_record(story=updated_story_text, name=story_info.name, last_update_date=now)
            if not rec.story:
                return
            db.TblStoryVersions.insert(delta=delta, 
                                       story_id=story_id, 
                                       creation_date=now,
                                       author_id=self.author_id
                                       )
        elif story_info.name != rec.name:
            rec.update_record(name=story_info.name, last_update_date=now, updater_id=self.author_id)
        update_story_words_index(story_id)
        author_name = auth.user_name(self.author_id)
        return Storage(story_id=story_id, last_update_date=now, updater_name=author_name, author=story_info.author)

    def find_translation(self, story_id, language):
        db = inject('db')
        q = (db.TblStories.translated_from==story_id) & (db.TblStories.language==language)
        return db(q).select().first()
    
    def find_story(self, used_for, topic):
        db = inject('db')
        q = (db.TblStories.used_for==used_for) & (db.TblStories.topic==topic)
        rec = db(q).select(db.TblStories.id).first()
        if rec:
            return self.get_story(rec.id)
        else:
            return None
        
    def get_all_stories(self, used_for):
        db = inject('db')
        q = (db.TblStories.used_for==used_for)
        for rec in db(q).select(db.TblStories.id):
            yield self.get_story(story_id)
            
    def set_used_for(self, story_id, used_for):
        db = inject('db')
        db(db.TblStories.id==story_id).update(used_for=used_for)
        
            
        