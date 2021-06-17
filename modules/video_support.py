from pytube import YouTube

from gluon.storage import Storage
from injections import inject


def youtube_info(src):
    url = "https://www.youtube.com/embed/" + src + "?wmode=opaque"
    comment = inject('comment')
    comment(f"youtube url is {url}")
    try:
        yt = YouTube(url)
    except:
        comment("got exception")
        return None
    try:
        result = Storage(title=yt.title,
                       thumbnail_url=yt.thumbnail_url,
                       description=yt.description,
                       author=yt.author,
                       publish_date=yt.publish_date)
    except:
        comment("failed to calc result")
        return None
    return result


def calc_youtube_info(video_id):
    db = inject('db')
    vrec = db(db.TblVideos.id == video_id).select().first()
    if (not vrec) or (vrec.video_type != 'youtube'):
        return
    info = youtube_info(vrec.src)
    if info:
        vrec.update_record(**info)
        return True
    return False


def calc_missing_youtube_info():
    db = inject('db')
    lst = db((db.TblVideos.video_type == 'youtube') & (db.TblVideos.deleted != True) & (
                db.TblVideos.thumbnail_url == None)).select(db.TblVideos.id)
    cnt = 0
    for vrec in lst[:50]:
        if calc_youtube_info(vrec.id):
            cnt += 1
    return dict(summray = f"{cnt} out of {len(lst)} videos calculated")
