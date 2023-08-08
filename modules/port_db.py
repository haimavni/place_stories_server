from http_utils import json_to_storage
import json
from injections import inject
import datetime

class Migrate:

    def __init(self):
        self.db = inject("db")
        self.categories = dict()

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
        plan = self.read_plan()
        for event in plan:
            if not event.items:
                continue #all items were duplicates
            self.create_event(event)
            # if len(event.items) > 1:
            #     story_id = self.create_story(event)
            # else:
            #     story_id = None
            # event_categories = event.categories

    def create_event(self, event):
        STORY4EVENT = inject("STORY4EVENT")
        if event.kind == "event":
            name = event.event_full_text
        elif event.kind == "ievent":
            name = event.event_name[7:]
        else:
            return None
        event_categories = event.categories
        # self.add_topics(event_categories, "E")
        text = event.read_more_text
        story_id = FileNotFoundError
        if len(event.items) > 1: # if only one item, give it the story
            story_id = self.db.insert(
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
        for item in event.items:
            self.create_item(event_categories, story_id, item)

    def create_item(self, event_categories, story_id, item):
        categories = item.categories or event_categories
        
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


