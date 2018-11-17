from docs_support import save_uploaded_doc

@serve_json
def upload_doc(vars):
    user_id = vars.user_id or auth.current_user()
    comment("start handling uploaded doc files")
    user_id = int(vars.user_id) if vars.user_id else auth.current_user()
    fil = vars.file
    result = save_uploaded_doc(fil.name, fil.BINvalue, user_id)
    return dict(upload_result=result)

