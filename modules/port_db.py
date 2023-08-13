from http_utils import json_to_storage
import json
from injections import inject
import datetime
from video_support import parse_video_url, youtube_info

class Migrate:

    def __init__(self):
        self.db = inject("db")
        self.categories = dict()

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

    def execute_plan(self):
        self.log_it("started to execute plan")
        plan = self.read_plan()
        plan_length = len(plan)
        self.log_it(f"{plan_length} events to port")
        count = 0
        for event in plan:
            if not event.event_items:
                continue #all event_items were duplicates
            self.create_event(event)
            count += 1
            # if len(event.event_items) > 1:
            #     story_id = self.create_story(event)
            # else:
            #     story_id = None
            # event_categories = event.categories
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
        if len(event.event_items) > 1: # if only one item, give it the story
            story_id = self.db.TblStories(
                used_for=STORY4EVENT,
                name=name,
                story=text,
                preview=text,
                story_date = datetime.date(year=event.year, month=1, day=1),
                source="ltl",
                creation_date=datetime.datetime.now(),
                story_len=len(text)
            )
            self.assign_topics(story_id, event_categories, "E")
        for item in event.event_items:
            self.create_item(event_categories, story_id, item)

    def create_item(self, event_categories, event_story_id, item):
        categories = item.categories or event_categories
        STORY4PHOTO, STORY4DOC, STORY4VIDEO = inject('STORY4PHOTO', 'STORY4DOC', 'STORY4VIDEO')
        usage = STORY4PHOTO if item.kind == "photo" else STORY4VIDEO if item.kind == "video" else STORY4DOC
        self.log_it("create item")
        db = self.db
        story_id = self.db.TblStories.insert(
            used_for=usage,
            name=item.title,
            story="",
            preview="",
            story_date = datetime.date(year=item.year, month=1, day=1),
            source="ltl",
            creation_date=datetime.datetime.now(),
            story_len=0
        )
        self.log_it(f"new story {story_id} {item.kind}")
        if item.kind == "photo":
            item_id = db.TblPhotos.insert(
                story_id=story_id,
                name=item.title, # todo: use only story name and remove this field
                photo_path=item.photo_path,
                photo_date=datetime.date(year=item.year, month=1, day=1),
            )
            if event_story_id: # connect photo to owning event
                db.TblEventPhotos.insert(item_id=item_id, story_id=event_story_id)
            categories = item.categories or event_categories
            self.assign_topics(story_id, categories, "P")
        elif item.kind == "pdf":
            item_id = db.TblDocs.insert(
                story_id=story_id,
                name=item.title, # todo: use only story name and remove this field
                doc_path=item.doc_path,
                doc_date=datetime.date(year=item.year, month=1, day=1),
            )
            if event_story_id: # connect doc to owning event
                db.TblEventDocs.insert(item_id=item_id, story_id=event_story_id)
            categories = item.categories or event_categories
            self.assign_topics(story_id, categories, "D")
        elif item.kind == "video":
            vid_info = parse_video_url(item.src)
            item_id = db.TblVideos.insert(
                story_id=story_id,
                name=item.title, # todo: use only story name and remove this field
                src=vid_info.src,
                upload_date=datetime.datetime.now(),
                video_type=vid_info.video_type,
                video_date=datetime.date(year=item.year, month=1, day=1),
            )
            if vid_info.video_type == "youtube":
                yt_info = youtube_info(item.src)
                db(db.TblVideos.id==item_id).update(
                    thumbnail_url=yt_info.thumbnail_url,
                    description=yt_info.description,
                    yt_upload_date=yt_info.upload_date,
                    uploader=yt_info.uploader,
                    duration=yt_info.duration,
                    )
            if event_story_id: # connect video to owning event
                db.TblEventVideos.insert(item_id=item_id, story_id=event_story_id)
            categories = item.categories or event_categories
            self.assign_topics(story_id, categories, "D")
        else:
            raise Exception("Unknown item kind")
        
    def add_topics(self, category_list, usage):
        db = self.db
        for cat in category_list:
            if cat not in self.categories:
                id = self.db.TblTopics.insert(name=cat, description="", usage=usage)
                self.categories[cat] = (id, usage)
            elif usage not in self.categories[cat][1]:
                id = self.categories[cat][0]
                rec = db(db.TblTopics.id==id).select().first()
                rec.update_record(usage=rec.usage + usage)
                
    def assign_topics(self, story_id, categories, usage):
        self.add_topics(categories, usage) 
        for cat in categories:
            topic_id = self.categories[cat] 
            self.db.TblItemTopics.insert(topic_id=topic_id, story_id=story_id, usage=usage)  


