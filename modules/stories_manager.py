import merge_in_memory as mim
import datetime
from injections import inject
from gluon.storage import Storage

def display_date(dt):
    return str(dt)[:19]

def get_display_version(num, sv):
    return '#{num} {dt} by {email}'.format(num=num, dt=display_date(sv.creation_time), email=sv.email)
    

class Stories:
    
    def __init__(self, author_id=None):
        if not author_id:
            auth = inject('auth')
            author_id = auth.current_user()
        self.author_id = author_id

    def get_story(self, story_id, from_story_version=None, to_story_version=None):
        db = inject('db')
        rec = db(db.TblStories.id==story_id).select(db.TblStories.story, db.TblStories.name).first()
        if not rec:
            return None
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
            name=rec.name,
            story_id=story_id,
            story_curr_version=to_story_version,
            story_versions=story_versions,
            display_version=display_version
        )
        return story_info

    def add_story(self, story_info):
        story_text = story_info.story_text
        name = story_info.name
        story_text = story_text.replace('~1', '&').replace('~2', ';').replace('\n', '').replace('>', '>\n')
        now = datetime.datetime.now()
        db, auth = inject('db', 'auth')
        author_name = auth.user_name(self.author_id)
        story_id = db.TblStories.insert(story=story_text, author_id=self.author_id, 
                                        name=name,
                                        used_for=story_info.used_for, 
                                        creation_date=now,
                                        last_update_date=now)
        return Storage(story_id=story_id, creation_date=now, author=author_name)

    def update_story(self, story_id, story_info):
        updated_story_text = story_info.story_text
        updated_story_text = updated_story_text.replace('~1', '&').replace('~2', ';').replace('\n', '').replace('>', '>\n')
        db, auth = inject('db', 'auth')
        rec = db(db.TblStories.id==story_id).select(db.TblStories.story).first()
        merger = mim.Merger()
        delta = merger.diff_make(rec.story, updated_story_text)
        db(db.TblStories.id==story_id).update(story=updated_story_text, name=story_info.name)
        if not rec.story:
            return
        now = datetime.datetime.now()
        db.TblStoryVersions.insert(delta=delta, 
                                   story_id=story_id, 
                                   creation_date=now,
                                   author_id=self.author_id
                                   )
        author_name = auth.user_name(self.author_id)
        return Storage(story_id=story_id, last_update_date=now, author=author_name)


