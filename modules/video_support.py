from youtube_dl import YoutubeDL
import stories_manager
from gluon.storage import Storage
from injections import inject


def youtube_info(src):
    url = "https://www.youtube.com/embed/" + src + "?wmode=opaque"
    comment = inject('comment')
    ydl = YoutubeDL()
    try:
        yt = ydl.extract_info(url, download=False)
    except:
        comment(f"ydl extract info of {url} got exception")
        return None
    try:
        result = Storage(title=yt['title'],
                         description=yt['description'],
                         uploader=yt['uploader'],
                         upload_date=yt['upload_date'])
    except Exception as e:
        comment(f"failed to calc result of {url}")
        return None
    return result


def calc_youtube_info(video_id):
    db, comment, STORY4VIDEO = inject('db', 'comment', 'STORY4VIDEO')
    vrec = db(db.TblVideos.id == video_id).select().first()
    if (not vrec) or (vrec.video_type != 'youtube'):
        return
    info = youtube_info(vrec.src)
    if info:
        vrec.update_record(**info)
        sm = stories_manager.Stories()
        video_story = sm.get_story(vrec.story_id)
        if not video_story:
            video_story = sm.get_empty_story(used_for=STORY4VIDEO)
        story_info = None
        if not video_story.story_text:
            story_info = Storage(story_text=vrec.description,
                                 preview=vrec.description)
        if not video_story.name:
            story_info = story_info or Storage()
            story_info.name = vrec.name or vrec.title
        if story_info:
            sm.update_story(vrec.story_id, story_info)
        return True
    return False


def calc_missing_youtube_info(count=10):
    db = inject('db')
    lst = db((db.TblVideos.video_type == 'youtube') & (db.TblVideos.deleted != True) & (
            db.TblVideos.description == None)).select(db.TblVideos.id)
    cnt = 0
    for vrec in lst[:count]:
        if calc_youtube_info(vrec.id):
            cnt += 1
        db.commit()
    return dict(summary=f"{cnt} out of {len(lst)} videos calculated")
