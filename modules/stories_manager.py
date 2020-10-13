from . import merge_in_memory as mim
import datetime
from .injections import inject
from gluon.storage import Storage
from .words import *
import re

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
        
    def get_story_rec(self, story_id):
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
        return rec

    def get_story(self, story_id, to_story_version=None, from_story_version=None):
        db, STORY4DOC = inject('db', 'STORY4DOC')
        rec = db(db.TblStories.id==story_id).select().first()
        if not rec:
            return None
        if self.language:  
            if rec.language != self.language:
                rec1 = self.find_translation(story_id, language)
                if rec1:
                    rec = rec1
                # else we have to read in the original language
        chatroom_id = rec.chatroom_id
        rec = Storage(rec)
        story = rec.story
        q = (db.TblStoryVersions.story_id==story_id)
        story_versions = db(q).select(db.TblStoryVersions.story_id, db.TblStoryVersions.creation_date, db.TblStoryVersions.author_id, db.TblStoryVersions.delta)
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
            if to_story_version < 0:
                to_story_version = max(current_version + to_story_version, 0)
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
        editable_preview = rec.used_for == STORY4DOC  #todo: better pass as parameter?
        if editable_preview:
            preview = rec.preview or get_reisha(story_text)
        else:
            preview = rec.preview or get_reisha(story_text) #todo: after all previews are set, can just use rec.preview
        story_info = Storage(
            story_text=story_text,
            preview=preview,
            editable_preview=editable_preview,
            name=rec.name,
            topic=rec.topic,
            story_id=story_id,   #we always access via the master
            source=rec.source,
            used_for=rec.used_for,
            author_id=rec.author_id,
            language=rec.language,
            story_curr_version=to_story_version,
            story_versions=story_versions,
            display_version=display_version,
            chatroom_id=rec.chatroom_id,
            approved_version=rec.approved_version,
            last_version=rec.last_version,
            last_update_date = rec.last_update_date,
            updater_id = rec.updater_id
        )
        return story_info
    
    def get_empty_story(self, used_for=2, story_text="New Story", name='stories.new-story'):
        story_info = Storage(
            story_text=story_text,
            preview=[],
            name=name,
            topic="",
            story_id="new",   #we always access via the master
            source="",
            used_for=used_for,
            author_id=None
            )
        return story_info

    def add_story(self, story_info, story_id=None, imported_from=''):
        story_text = story_info.story_text
        name = story_info.name
        language = guess_language(name + ' ' + story_text)
        story_text = story_text.replace('~1', '&').replace('~2', ';').replace('\n', '').replace('>', '>\n')
        now = datetime.datetime.now()
        db, auth, STORY4EVENT, STORY4TERM, STORY4PHOTO, STORY4DOC, STORY4AUDIO, TEXT_AUDITOR = inject('db', 'auth', 'STORY4EVENT', 'STORY4TERM', 'STORY4PHOTO', 'STORY4DOC', 'STORY4AUDIO', 'TEXT_AUDITOR')
        source = story_info.source
        ###todo: handle language issues here and in update_story
        story_id = db.TblStories.insert(story=story_text, 
                                        author_id=self.author_id, 
                                        name=name,
                                        source=source,
                                        used_for=story_info.used_for,
                                        translated_from=story_id,
                                        creation_date=now,
                                        language=language,
                                        topic=story_info.topic,
                                        last_version=0,
                                        approved_version=0 if auth.user_has_privilege(TEXT_AUDITOR) else -1,
                                        last_update_date=now,
                                        imported_from=imported_from)
        preview = get_reisha(story_text)
        db(db.TblStories.id==story_id).update(preview=preview)
        if story_info.used_for == STORY4EVENT:
            db.TblEvents.insert(
                story_id=story_id,
                Name=name,
            )
        elif story_info.used_for == STORY4TERM:    
            db.TblTerms.insert(
                story_id=story_id,
                Name=name,
            )
        elif story_info.used_for == STORY4PHOTO:
            pass
        
        ###update_story_words_index(story_id)
        promote_word_indexing()
        return Storage(story_id=story_id, creation_date=now, author=source, preview=preview, name=name)

    def update_story(self, story_id, story_info, language=None, change_language=False, imported_from=''):
        db, auth, STORY4EVENT, STORY4TERM, STORY4PHOTO, STORY4DOC, STORY4AUDIO, TEXT_AUDITOR = inject('db', 'auth', 'STORY4EVENT', 'STORY4TERM', 'STORY4PHOTO', 'STORY4DOC', 'STORY4AUDIO', 'TEXT_AUDITOR')
        if story_id == 'new':
            return self.add_story(story_info)
        updated_story_text = story_info.story_text
        rec = db(db.TblStories.id==story_id).select().first()
        if language:
            rec = self.find_translation(rec, language)
            if not rec:
                self.create_translation(story_id, language)
        if len(updated_story_text) > 20:
            language1 = guess_language(updated_story_text)
            if language1 == 'UNKNOWN':
                language1 = guess_language(story_info.preview)
        else:
            language1 = 'he'  #todo: use default user's language
        #todo: the following is not yet implemented in the client, where it should as the user
        #if rec.language and rec.language != 'UNKNOWN' and language1 != rec.language and not change_language:
            #return Storage(language_changed=True)
        updated_story_text = updated_story_text.replace('~1', '&').replace('~2', ';').replace('\n', '').replace('>', '>\n')
        #if rec.language and rec.language != language:
            #rec = self.find_translation(rec, language)
        now = datetime.datetime.now()
        preview = ''
        if story_info.used_for == STORY4DOC:
            if not story_info.preview:
                story_info.preview = get_reisha(updated_story_text)
            preview = story_info.preview
            data = Storage(last_update_date=now, story_text=updated_story_text)
            if story_info.preview and rec.preview != story_info.preview:
                data.preview = story_info.preview
            else:
                data.preview = rec.preview
            if story_info.name and rec.name != story_info.name:
                data.name = story_info.name
            else:
                data.name = rec.name
            data.source = story_info.source
            rec.update_record(**data)
        elif rec.story != updated_story_text:
            merger = mim.Merger()
            delta = merger.diff_make(rec.story, updated_story_text)
            last_version = db((db.TblStoryVersions.story_id==story_id)&(db.TblStoryVersions.language==rec.language)).count() + 1
            preview = get_reisha(updated_story_text)
            if imported_from and not rec.imported_from:
                imported_from = imported_from.upper() #signal import overrides previous content
            data = dict(
                story=updated_story_text,
                preview=preview,
                name=story_info.name, 
                source=story_info.source, 
                last_update_date=now, 
                updater_id=self.author_id,
                last_version=last_version,
                language=language1,
                imported_from=imported_from,
                sorting_key=story_info.sorting_key
            )
            text_auditor = auth.user_has_privilege(TEXT_AUDITOR)
            if text_auditor:
                data['approved_version'] = last_version
            rec.update_record(**data)
            db.TblStoryVersions.insert(
                delta=delta, 
                story_id=story_id, 
                creation_date=now,
                author_id=self.author_id,
                language=language1)
        elif story_info.name != rec.name or story_info.source != rec.source or story_info.sorting_key != rec.sorting_key:
            rec.update_record(name=story_info.name, source=story_info.source, last_update_date=now, updater_id=self.author_id)
        ###update_story_words_index(story_id)
        author_name = auth.user_name(self.author_id) #name of the mblbhd, not the source
        name = story_info.name
        if story_info.used_for == STORY4EVENT:
            rec = db(db.TblEvents.story_id==story_id).select().first()
            if rec:
                rec.update_record(Name=name)
        elif story_info.used_for == STORY4TERM:    
            rec = db(db.TblTerms.story_id==story_id).select().first()
            if rec:
                rec.update_record(Name=name)
        elif story_info.used_for == STORY4PHOTO:
            photo_rec = db(db.TblPhotos.story_id==story_id).select().first()
            photo_rec.update_record(Name=name)
        elif story_info.used_for == STORY4AUDIO:
            audio_rec = db(db.TblAudios.story_id==story_id).select().first()
            audio_rec.update_record(name=name)
        promote_word_indexing()
        return Storage(story_id=story_id, last_update_date=now, updater_name=author_name, author=story_info.source, language=language, name=name, preview=preview)
    
    def update_story_name(self, story_id, new_name, language=None):
        db = inject('db')
        rec = db(db.TblStories.id==story_id).select().first()
        if language:
            rec = self.find_translation(rec, language)
        if rec:
            rec.update_record(name=new_name)
        #promote indexing task
        
    def find_translation(self, story_id, language=None):
        db = inject('db')
        if language:
            q = (db.TblStories.translated_from==story_id) & (db.TblStories.language==language)
        else:
            q = db.TblStories.id==story_id
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
        
    def approve_story(self, story_id, language=None):
        story_info = self.get_story(story_id)
        rec = self.find_translation(story_id, language)
        
    def delete_story(self, story_id):
        db = inject('db')
        now = datetime.datetime.now()
        db(db.TblStories.id==story_id).update(deleted=True, last_update_date=now)
        promote_word_indexing()
        
def promote_word_indexing():
    promote_task = inject('promote_task')
    promote_task('update_word_index_all')
    
def mark_diffs(txt1, txt2):
    txt1 = handle_html_tags(txt1)
    txt2 = handle_html_tags(txt2)
    merger = mim.Merger()
    delta = merger.diff_make(txt1, txt2)
    txt1_lst = txt1.split('\n')
    pat = r'@@ -'
    diffs = re.split(pat, delta)
    diffs = diffs[1:]
    diffs.reverse()
    for dif in diffs:
        lst = dif.split('\n')
        idx, span = calc_idx_span(lst[0])
        if idx > 0:
            idx -= 1
        else:
            dbg = 999
        marked_rows = mark_marked_rows(lst[1:])
        txt1_lst[idx:idx+span] = marked_rows
    txt1 = '\n'.join(txt1_lst)
    return txt1

def handle_html_tags(txt):
    pat = r'<.*?>|[^<>]*'
    txt = txt.replace('\n', '')
    lst = re.findall(pat, txt)
    result = ''
    for s in lst:
        if s.startswith('<'):
            result += s + '\n'
        else:
            result += break_str(s, 50)
    result += s
    result.replace('\n', '')
    return result

def break_str(txt, lim):
    lst = txt.split()
    result = ''
    row = ''
    n = 0
    for wrd in lst:
        row += wrd
        if len(row) > lim:
            result += row + '\n'
            row = ''
        else:
            row += ' '
    if row:
        result += row + '\n'
    return result
    
def calc_idx_span(s):
    lst = re.findall(r'\d+', s)
    idx, span = int(lst[0]), int(lst[1])
    return idx, span
  
def mark_marked_rows(lst):
    result = []
    state = 0
    for s in lst:
        if s.startswith('-') and '<' not in s:
            if state == 2:
                result[-1] = result[-1] + '</span>'
            s = s[1:]
            if state != 1:
                s = '<span class="removed">' + s
            state = 1
        elif s.startswith('+') and '<' not in s:
            if state == 1:
                result[-1] = result[-1] + '</span>'
            s = s[1:]
            if state != 2:
                s = '<span class="added">' + s
            state = 2
        else:
            if state:
                result[-1] = result[-1] + '</span>'
            state = 0
        if s.startswith('-') or s.startswith('+'):
            s = s[1:]
        result.append(s)
        
    if state:
        result += '</span>'
    return result
    