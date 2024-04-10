from http_utils import json_to_storage
import json
from injections import inject
import datetime
from video_support import parse_video_url, youtube_info
from words import get_reisha

class Migrate:

    def __init__(self):
        self.db = inject("db")

    def log_it(self, s):
        my_log = inject("my_log")
        my_log(s, file_name="port_db.log")

    def read_plan(self):
        request = inject("request")
        app = request.application
        r = app.find("__")
        if r > 0:
            app = app[:r]
        fname = f"/apps_data/{app}/plan.txt"
        with open(fname, "r", encoding="utf-8") as f:
            data = f.read()
        obj = json.loads(data)
        result = json_to_storage(obj)
        return result

    def execute_plan(self, first=0, limit=1000):
        db = inject("db")
        self.log_it("started to execute plan")
        plan = self.read_plan()
        plan_length = len(plan)
        plan = plan[first:first+limit]
        last = first + limit
        self.log_it(f"{plan_length} events to port")
        self.log_it(f"events between {first} and {last}")
        count = 0
        for event in plan:
            n = len(event.event_items)
            self.log_it(f"{n} items in event {count}")
            if not event.event_items:
                continue #all event_items were duplicates
            self.create_event(event)
            count += 1
        db.commit()
        return f"{count} events were processed."

    def create_event(self, event):
        STORY4EVENT = inject("STORY4EVENT")
        if event.kind == "event":
            name = event.event_full_text
        elif event.kind == "ievent":
            name = event.event_name[7:]
        else:
            return None
        event_categories = event.categories
        text = event.read_more_text
        story_id = None
        event_id = None
        self.log_it(f"-----------number of items: {len(event.event_items)}")
        if len(event.event_items) > 1: # if only one item, give it the story
            story_id = self.db.TblStories.insert(
                used_for=STORY4EVENT,
                name=name,
                story=text,
                preview=text,
                story_date=datetime.date(year=int(event.year), month=1, day=1),
                story_date_dateend=datetime.date(year=int(event.year), month=1, day=1),
                source="ltl",
                creation_date=datetime.datetime.now(),
                story_len=len(text),
                visibility=1
            )
            event_id = self.db.TblEvents.insert(
                story_id=story_id,
                event_date=datetime.date(year=int(event.year), month=1, day=1),
                event_date_dateend=datetime.date(year=int(event.year), month=1, day=1)
            )
            self.log_it(f"story id is: {story_id}")
            self.assign_topics(story_id, event_categories, "E")
        for item in event.event_items:
            self.create_item(event_categories, event_id, item)
            #self.connect_item(event_id, item) # was used to fix previous issue
            
    def connect_item(self, event_id, item):
        db = self.db
        if not event_id:
            return
        if item.kind == "image":
            photo_id = db(db.TblPhotos.photo_path==item.photo_path).select().first().id
            db.TblEventPhotos.insert(photo_id=photo_id, event_id=event_id)
        elif item.kind == "pdf":
            doc_id = db(db.TblDocs.doc_path==item.doc_path).select().first().id
            db.TblEventDocs.insert(doc_id=doc_id, event_id=event_id)
        elif item.kind == "video":
            vid_info = parse_video_url(item.src)
            video_id = db(db.TblVideos.src==vid_info.src).select().first().id
            db.TblEventVideos.insert(video_id=video_id, event_id=event_id)
        

    def create_item(self, event_categories, event_id, item):
        categories = item.categories or event_categories
        STORY4PHOTO, STORY4DOC, STORY4VIDEO, STORY4EVENT = inject('STORY4PHOTO', 'STORY4DOC', 'STORY4VIDEO', 'STORY4EVENT')
        usage = STORY4PHOTO if item.kind == "image" else STORY4VIDEO if item.kind == "video" else STORY4DOC if item.kind == "pdf" else STORY4EVENT
        self.log_it("create item")
        if item.kind == "text":
            story_text = item["html"]
            preview = get_reisha(story_text)
        else:
            story_text = ""
            preview = ""
        db = self.db
        story_id = self.db.TblStories.insert(
            used_for=usage,
            name=item.title,
            story=story_text,
            preview=preview,
            story_date = datetime.date(year=int(item.year), month=1, day=1),
            story_date_dateend = datetime.date(year=int(item.year), month=1, day=1),
            source="ltl",
            creation_date=datetime.datetime.now(),
            story_len=len(story_text),
            visibility=1
        )
        self.log_it(f"new story {story_id} {item.kind}")
        if item.kind == "image":
            photo_id = db.TblPhotos.insert(
                story_id=story_id,
                name=item.title, 
                recognized=True,
                # todo: use only story name and remove this field
                photo_path=item.photo_path,
                original_file_name=item.photo_path,
                photo_date=datetime.date(year=int(item.year), month=1, day=1),
                photo_date_dateend=datetime.date(year=int(item.year), month=1, day=1)
            )
            if event_id: # connect photo to owning event
                db.TblEventPhotos.insert(photo_id=photo_id, event_id=event_id)
            categories = item.categories or event_categories
            self.assign_topics(story_id, categories, "P")
        elif item.kind == "pdf":
            doc_id = db.TblDocs.insert(
                story_id=story_id,
                name=item.title, # todo: use only story name and remove this field
                doc_path=item.doc_path,
                doc_date=datetime.date(year=int(item.year), month=1, day=1),
                doc_date_dateend=datetime.date(year=int(item.year), month=1, day=1)
                
            )
            if event_id: # connect doc to owning event
                db.TblEventDocs.insert(doc_id=doc_id, event_id=event_id)
            categories = item.categories or event_categories
            self.assign_topics(story_id, categories, "D")
        elif item.kind == "video":
            self.log_it(f" video src is {item.src}")
            vid_info = parse_video_url(item.src)
            video_id = db.TblVideos.insert(
                story_id=story_id,
                name=item.title, # todo: use only story name and remove this field
                src=vid_info.src,
                upload_date=datetime.datetime.now(),
                video_type=vid_info.video_type,
                video_date=datetime.date(year=int(item.year), month=1, day=1),
                video_date_dateend=datetime.date(year=int(item.year), month=1, day=1)
            )
            if vid_info.video_type == "youtube":
                yt_info = youtube_info(vid_info.src)
                if yt_info:
                    db(db.TblVideos.id==video_id).update(
                        thumbnail_url=yt_info.thumbnail_url,
                        description=yt_info.description,
                        yt_upload_date=yt_info.upload_date,
                        uploader=yt_info.uploader,
                        duration=yt_info.duration,
                        )
                else:
                    self.log_it(f"No yt info for video id {video_id}")
            if event_id: # connect video to owning event
                db.TblEventVideos.insert(video_id=video_id, event_id=event_id)
            categories = item.categories or event_categories
            self.assign_topics(story_id, categories, "V")
        elif item.kind == "text":
            db.TblEvents.insert(story_id=story_id,
                                name=item.title)
            categories = item.categories or event_categories
            self.assign_topics(story_id, categories, "E")
        else:
            raise Exception(f"Unknown item kind {item.kind}")
        
    def add_topics(self, category_list, usage):
        db = self.db
        for cat in category_list:
            rec = db(db.TblTopics.name==cat).select().first()
            if rec:
                if usage not in rec.usage:
                    rec.update_record(usage=rec.usage + usage)
            else:
                self.db.TblTopics.insert(name=cat, description="", usage=usage, topic_kind=2)

    def assign_topics(self, story_id, categories, usage):
        db = self.db
        self.add_topics(categories, usage) 
        for cat in categories:
            topic_id = db(db.TblTopics.name==cat).select().first().id
            self.db.TblItemTopics.insert(topic_id=topic_id, story_id=story_id, usage=usage)
            
    def start_from_scratch(self):
        db = self.db
        db.TblTopics.truncate('RESTART IDENTITY CASCADE')
        db.TblItemTopics.truncate('RESTART IDENTITY CASCADE')
        db.TblStories.truncate('RESTART IDENTITY CASCADE')
        db.TblPhotos.truncate('RESTART IDENTITY CASCADE')
        db.TblEventPhotos.truncate('RESTART IDENTITY CASCADE')
        db.TblDocs.truncate('RESTART IDENTITY CASCADE')
        db.TblEventDocs.truncate('RESTART IDENTITY CASCADE')
        db.TblVideos.truncate('RESTART IDENTITY CASCADE')
        db.TblEventVideos.truncate('RESTART IDENTITY CASCADE')

