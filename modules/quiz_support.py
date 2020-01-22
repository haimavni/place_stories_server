from injections import inject

def apply_quiz(items, answers):
    '''
    items is a list of object ids to be assigned.
    answers is a list of answer ids selected by the user
    '''
    db = inject('db')
    for ans_id in answers:
        question_id = db(db.TblAnswers.id==ans_id).select().first().question_id
        q = (db.TblAnswers.question_id==question_id) & (db.TblItemAnswers.item_id.belongs(items)) & (db.TblItemAnswers.answer_id==db.TblAnswers.id)
        lst = db(q).select()
        old_items = set([])
        #update existing items where answer might have changed
        for rec in lst:
            item_rec = rec.TblItemAnswers
            db(db.TblItemAnswers.id==item_rec.id).update(answer_id=ans_id)
            old_items.add(item_rec.item_id)
        #create items that did not exist
        for itm in items:
            if itm in old_items:
                continue
            db.TblItemAnswers.insert(item_id=itm, answer_id=ans_id)
            
def use_quiz(answers):
    db = inject('db')
    lst = db(db.TblAnswers.id.belongs(answers)).select(orderby=db.TblAnswers.question_id)
    group = []
    group_arr = []
    prev_question = -1
    for rec in lst:
        if rec.question_id != prev_question:
            if group:
                group_arr += [group]
                prev_question = rec.question_id
                group = []
        group += [rec.id]
    group_arr += [group]
    item_set = None
    for group in group_arr:
        items = db(db.TblItemAnswers.answer_id.belongs(group)).select()
        item_arr = [rec.item_id for rec in items]
        if item_set:
            item_set &= set(item_arr)
        else:
            item_set = set(item_arr)
    result = [itm for itm in item_set]
    return result
    