from quiz_support import apply_quiz

@serve_json
def read_menu(vars):
    name = vars.name
    menu = db(db.TblMenus.name == name).select().first()
    if menu:
        menu_id = menu.id
    else:
        menu_id = db.TblMenus.insert(name=name)
    q = db.TblQuestions.menu_id==menu_id
    lst = db(q).select()
    result = []
    for rec in lst:
        question = rec
        answers = db(db.TblAnswers.question_id==rec.id).select()
        answers = [dict(aid=ans.id, qid=rec.id, text=ans.text) for ans in answers]
        prompt = question.prompt
        result.append(dict(prompt=prompt, qid=question.id, answers = answers or []))
    return dict(questions=result)

@serve_json
def save_question(vars):
    name = vars.name
    prompt = vars.prompt
    question_id = vars.question_id
    menu = db(db.TblMenus.name == name).select().first()
    if menu:
        menu_id = menu.id
    else:
        menu_id = db.TblMenus.insert(name=name)
    if question_id:
        db(db.TblQuestions.id == question_id).update(prompt=prompt)
    else:
        question_id = db.TblQuestions.insert(menu_id=menu_id, prompt=prompt)
    return dict(question_id=question_id)

@serve_json
def save_answer(vars):
    question_id = vars.question_id
    answer_id = vars.answer_id
    text = vars.text
    if answer_id:
        db(db.TblAnswers.id==answer_id).update(text=text)
    else:
        answer_id = db.TblAnswers.insert(question_id=question_id, text=text)
    return dict(answer_id=answer_id)

@serve_json
def apply_answers(vars):
    checked_answers = vars.checked_answers
    item_list = vars.item_list
    apply_quiz(item_list, checked_answers)
    return dict()