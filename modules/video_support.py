from yt_dlp import YoutubeDL
import stories_manager
from gluon.storage import Storage
from injections import inject
import datetime
import re
from pythumb import Thumbnail
from folders import local_photos_folder, url_of_local_path
from photos_support import save_padded_photo


def youtube_info(src):
    url = "https://www.youtube.com/embed/" + src + "?wmode=opaque"
    log_exception = inject('log_exception')
    thumbnail_url=f"https://i.ytimg.com/vi/{src}/mq2.jpg"
    now = datetime.datetime.now()
    timestamp = int(round(now.timestamp()))
    thumbnail_url += f"?d={timestamp}" #so user will not see cached thumnail
    result = Storage(thumbnail_url=thumbnail_url)
    ydl = YoutubeDL()
    try:
        yt = ydl.extract_info(url, download=False)
    except Exception as e:
        log_exception(f"ydl extract info of {url} got exception")
        return result
    result = Storage(title=yt['title'],
                     description=yt['description'],
                     uploader=yt['uploader'],
                     duration=yt['duration'],
                     thumbnail_url=thumbnail_url,
                     upload_date=yt['upload_date'])
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
            db.TblVideos.thumbnail_url == None)).select(db.TblVideos.id)
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

def update_video_thumbnails():
    db, comment = inject('db', 'comment')
    comment("-----------started update video thumbnails")
    q = (db.TblVideos.video_type == 'youtube') & (db.TblVideos.deleted != True)
    q &= (db.TblVideos.thumbnail_url==None) | (db.TblVideos.thumbnail_url=="")
    n = db(q).count()
    comment(f"{n} videos need fix")
    for vrec in db(q).select():
        vrec.update_record(thumbnail_url=f"https://i.ytimg.com/vi/{vrec.src}/mq2.jpg")
    return "done"
        

def update_cuepoints_text(video_id):
    db = inject('db')
    vid_rec = db(db.TblVideos.id==video_id).select().first()
    result = ""
    for cuepoint in db(db.TblVideoCuePoints.video_id==video_id).select():
        result += cuepoint.description + ' '
    vid_rec.update_record(cuepoints_text=result)
    return result

def parse_video_url(input_url):
    pats = dict(
        youtube=r'https://(?:www.youtube.com/(?:watch\?v=|embed/)|youtu\.be/)(?P<code>[^&?]+).*',
        html5=r'(?P<code>.+\.mp4)',
        vimeo=r'https://vimeo.com/(?P<code>\d+)',
        google_drive=r'https://drive.google.com/file/d/(?P<code>[^/]+?)/.*',
        google_photos=r'https://photos.app.goo.gl/(?P<code>[^&]+)'
    )
    src = None
    for t in pats:
        pat = pats[t]
        m = re.search(pat, input_url)
        if m:
            src = m.groupdict()['code']
            typ = t
            break
    if not src:
        typ = "raw"
        src = input_url
        # User_Error = inject("User_Error")
        # raise User_Error('!videos.unknown-video-type')
    return Storage(src=src, video_type=typ)

def save_yt_thumbnail(src):
    t = Thumbnail(src)
    t.fetch()
    folder = local_photos_folder("padded")
    path = t.save(folder)
    r = path.rfind("/")
    path = folder + path[r+1:]
    target_path = path.replace(".", "-padded.")
    save_padded_photo(path, target_path, width=227, height=133, color=0)
    url = url_of_local_path(target_path)
    return dict(target_path=target_path, url=url, path=path)
