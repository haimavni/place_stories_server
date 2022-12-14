from youtube_dl import YoutubeDL
import stories_manager
from gluon.storage import Storage
from injections import inject


def youtube_info(src):
    url = "https://www.youtube.com/embed/" + src + "?wmode=opaque"
    comment, log_exception = inject('comment', 'log_exception')
    ydl = YoutubeDL()
    try:
        yt = ydl.extract_info(url, download=False)
    except Exception as e:
        comment(f"ydl extract info of {url} got exception {e}")
        return None
    try:
        comment(f"still alive. thumbnails in yt? {'thumbnails' in yt} ")
        thumbnails = yt['thumbnails']
        comment(f"still alive {len(thumbnails)}")
        #comment(f"thumbnails: {thumbnails}")
        try:
            comment("before 3")
            thumbnail_url = thumbnails[3]
            comment("after 3")
        except Exception as e:
            comment(f"thumbnails: {thumbnails}")
        comment("still alive the zona")
        #comment(f"thumbnail_url: {thumbnail_url}")

        result = Storage(title=yt['title'],
                         description=yt['description'],
                         uploader=yt['uploader'],
                         duration=yt['duration'],
                         thumbnail_url=thumbnail_url,
                         upload_date=yt['upload_date'])
    except Exception as e:
        log_exception('zevel')
        comment(f"failed to calc result of {url}: {e}")
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
        story_info = Storage(story_text=video_story.story_text or vrec.description,
                             name=video_story.name or vrec.name or vrec.title)
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

def upgrade_youtube_info(chunk=10):
    db = inject('db')
    lst = db((db.TblVideos.video_type == 'youtube') & \
        (db.TblVideos.deleted != True) & \
            (db.TblVideos.duration==None)).select(limitby=(0, chunk))
    bad = 0
    good = 0
    for vrec in lst:
        yt_info = youtube_info(vrec.src)
        if yt_info:
            good += 1
            vrec.update_record(duration=yt_info.duration, thumbnail_url=yt_info.thumbnail_url)
        else:
            bad += 1
    return Storage(total=len(lst), bad=bad, good=good)

