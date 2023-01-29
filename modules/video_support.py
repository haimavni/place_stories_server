from youtube_dl import YoutubeDL
import stories_manager
from gluon.storage import Storage
from injections import inject
import datetime


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
        thumbnails = yt['thumbnails']
        try:
            thumbnail_url = thumbnails[3]['url']
        except Exception as e:
            log_exception('thumbnail url')
        now = datetime.datetime.now()
        timestamp = int(round(now.timestamp()))
        thumbnail_url += f"?d={timestamp}" #so user will not see cached thumnail
        result = Storage(title=yt['title'],
                         description=yt['description'],
                         uploader=yt['uploader'],
                         duration=yt['duration'],
                         thumbnail_url=thumbnail_url,
                         upload_date=yt['upload_date'])
    except Exception as e:
        log_exception('youtube info')
        return None
    return result


def calc_youtube_info(video_id):
    db, STORY4VIDEO = inject('db', 'STORY4VIDEO')
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

def upgrade_youtube_info(chunk=50, video_list=None):
    db, comment, log_exception = inject('db', 'comment', 'log_exception')
    q = (db.TblVideos.video_type == 'youtube') & (db.TblVideos.deleted != True)
    if video_list:
        q &= (db.TblVideos.id.belongs(video_list))
    else:
        q &= (db.TblVideos.duration==None)
    try:
        total = db(q).count()
    except Exception as e:
        log_exception(f"upgrade youtube info for [{video_list}]")
        comment(f"upgrade youtube info failed for [{video_list}]")
        return dict()
    comment(f"upgrade youtube info succeeded for [{video_list}]")
    lst = db(q).select(limitby=(0, chunk))
    bad = 0
    good = 0
    for vrec in lst:
        yt_info = youtube_info(vrec.src)
        if yt_info:
            good += 1
            vrec.update_record(duration=yt_info.duration, thumbnail_url=yt_info.thumbnail_url)
        else:
            bad += 1
    return Storage(total=total, bad=bad, good=good)

def update_cuepoints_text(video_id):
    db = inject('db')
    vid_rec = db(db.TblVideos.id==video_id).select().first()
    result = ""
    for cuepoint in db(db.TblVideoCuePoints.video_id==video_id).select():
        result += cuepoint.description + ' '
    vid_rec.update_record(cuepoints_text=result)
    return result



