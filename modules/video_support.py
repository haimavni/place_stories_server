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
    x = dir(yt)
    comment(f"dir of yt: {x}")
    comment(f"thumbnail: {yt.thumbnail_url}")
    comment(f"description: {yt.description}")
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


def calc_missing_youtube_info(count=10):
    db = inject('db')
    lst = db((db.TblVideos.video_type == 'youtube') & (db.TblVideos.deleted != True) & (
                db.TblVideos.thumbnail_url == None)).select(db.TblVideos.id)
    cnt = 0
    for vrec in lst[:count]:
        if calc_youtube_info(vrec.id):
            cnt += 1
        db.commit()
    return dict(summray = f"{cnt} out of {len(lst)} videos calculated")
