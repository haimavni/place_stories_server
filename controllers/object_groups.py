class ObjectGroups:
    
    def __init__(self, what, user_id):
        self.what = what
        self.user_id = user_id
        
    def get_group_list(self):
        lst = db((db.TblUserObjectGroups.user_id==self.user_id) & (db.TblUserObjectGroups.what==self.what)).select()
        lst = [(rec.id, rec.name) for rec in lst]
        return lst
    
    def get_add_group(self, name):
        group = db((db.TblUserObjectGroups.name==name) & (db.TblUserObjectGroups.what==self.what)).select().first()
        if group:
            group_id = group.id
        else:
            group_id = db.TblUserObjectGroups.insert(user_id=self.user_id, what=self.what, name=name)
        return group_id
    
    def get_group_items(self, group_id):
        lst = db(db.TblUserObjectGroupItems.id==group_id)
        lst = [rec.id for rec in lst]
        return lst
    
    def save_group_items(self, group_id, item_ids):
        old_ids = self.get_group_items(group_id)
        for item_id in item_ids:
            if item_id not in old_ids:
                db.TblUserObjectGroupItems.insert(item_id=item_id, group_id=group_id)
        for item_id in old_ids:
            if item_id not in item_ids:
                db((db.TblUserObjectGroupItems.item_id==item_id) & (db.TblUserObjectGroupItems.group_id==group_id)).delete()
        
@serve_json
def get_member_group_list(vars):
    user_id = vars.user_id
    og = ObjectGroups('Members', user_id)
    return dict(groups=og.get_group_list())

@serve_json
def save_group_members(vars):
    user_id = vars.user_id
    og = ObjectGroups('Members', user_id)
    group_id = vars.group_id
    member_ids = vars.member_ids
    og.save_group_items(group_id, member_ids)
    return dict()
    
@serve_json
def get_group_members(vars):
    user_id = vars.user_id
    og = ObjectGroups('Members', user_id)
    group_id = vars.group_id
    group_member_ids = og.get_group_items(group_id)
    return dict(group_member_ids=group_member_ids)
    
    