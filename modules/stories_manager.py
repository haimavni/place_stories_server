import merge_in_memory as mim
import datetime
from injections import inject
from gluon.storage import Storage

def display_date(dt):
    return str(dt)[:19]

def get_display_version(num, sv):
    return '#{num} {dt} by {email}'.format(num=num, dt=display_date(sv.creation_time), email=sv.email)
    

class Stories:

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
            sv.email = db(db.auth_user.id==sv.author_id).select(db.auth_user.email).first().email
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

    def add_story(self, story, used_for):
        db, auth = inject('db', 'auth' )
        story_id = db.TblStories.insert(story=story, author_id=auth.current_user(), used_for=used_for, creation_date=datetime.datetime.now())
        return story_id

    def update_story(self, story_id, updated_story):
        db, auth = inject('db', 'auth')
        db(db.TblStories.id==story_id).update(story=updated_story)
        merger = mim.Merger()
        rec = db(db.TblStories.id==story_id).select(db.TblStories.story).first()
        if not rec.story:
            return
        delta = merger.diff_make(rec.story, updated_story)
        db.TblStoryVersions.insert(delta=delta, 
                                   story_id=story_id, 
                                   creation_date=datetime.datetime.now(),
                                   author_id=auth.current_user()
                                   )


