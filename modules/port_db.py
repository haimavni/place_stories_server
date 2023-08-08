from http_utils import json_to_storage
import json
from injections import inject

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
                continue
            if len(event.items) > 1:
                story_id = self.create_story(event)
            else:
                story_id = None

    def create_story(self, event):
        if event.kind == "event":
            name = event.event_full_text
        elif event.kind == "ievent":
            name = event.event_name[7:]
        else:
            return None
        text = event.read_more_text
        story_id = self.db.insert(
            name=name
        )


