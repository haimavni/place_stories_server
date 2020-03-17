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
    lst = db(q).select(orderby=db.TblQuestions.id)
    result = []
    for rec in lst:
        question = rec
        answers = db(db.TblAnswers.question_id==rec.id).select(orderby=db.TblAnswers.id)
        answers = [dict(aid=ans.id, qid=rec.id, text=ans.text, description=ans.description) for ans in answers]
        result.append(dict(prompt=question.prompt, description=question.description, qid=question.id, answers = answers or []))
    return dict(questions=result)

@serve_json
def save_question(vars):
    name = vars.name
    prompt = vars.prompt
    description = vars.description
    question_id = vars.question_id
    menu = db(db.TblMenus.name == name).select().first()
    if menu:
        menu_id = menu.id
    else:
        menu_id = db.TblMenus.insert(name=name)
    if question_id:
        db(db.TblQuestions.id == question_id).update(prompt=prompt, description=description)
    else:
        question_id = db.TblQuestions.insert(menu_id=menu_id, prompt=prompt, description=description)
    return dict(question_id=question_id)

@serve_json
def save_answer(vars):
    question_id = vars.question_id
    answer_id = vars.answer_id
    text = vars.text
    description = vars.description
    if answer_id:
        db(db.TblAnswers.id==answer_id).update(text=text, description=description)
    else:
        answer_id = db.TblAnswers.insert(question_id=question_id, text=text, description=description)
    return dict(answer_id=answer_id)

@serve_json
def apply_answers(vars):
    checked_answers = vars.checked_answers
    item_list = vars.item_list
    apply_quiz(item_list, checked_answers)
    return dict()