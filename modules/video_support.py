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
    except Exception as e:
        comment(f"ydl extract info of {url} got exception {e}")
        return None
    try:
        yt_keys = yt.keys()
        comment(f"youtube info keys: {yt_keys}")
        #['id', 'title', 'formats', 'thumbnails', 'description', 'upload_date', 'uploader', 'uploader_id', 'uploader_url', 
        # 'channel_id', 'channel_url', 'duration', 'view_count', 'average_rating', 'age_limit', 'webpage_url', 
        # 'categories', 'tags', 'is_live', 'channel', 'extractor', 'webpage_url_basename', 'extractor_key', 'playlist', 
        # 'playlist_index', 'thumbnail', 'display_id', 'requested_subtitles', 'requested_formats', 'format', 'format_id', 
        # 'width', 'height', 'resolution', 'fps', 'vcodec', 'vbr', 'stretched_ratio', 'acodec', 'abr', 'ext'])
        result = Storage(title=yt['title'],
                         description=yt['description'],
                         uploader=yt['uploader'],
                         duration=yt['duration'],
                         thumbnail=yt['thumbnail'],
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
