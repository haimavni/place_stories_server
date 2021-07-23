from youtube_dl import YoutubeDL

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
    db, comment = inject('db', 'comment')
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
            db.TblVideos.description == None)).select(db.TblVideos.id)
    cnt = 0
    for vrec in lst[:count]:
        if calc_youtube_info(vrec.id):
            cnt += 1
        db.commit()
    return dict(summray=f"{cnt} out of {len(lst)} videos calculated")
