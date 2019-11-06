from admin_support.access_manager import register_new_user, AccessManager

def init_database():
    if len(request.args) < 4:
        return "database initialized without admin"
    email,password,first_name,last_name = request.args
    usr_id = register_new_user(email, password, first_name, last_name)
    am = AccessManager()
    am.enable_all_roles(usr_id)
    db.commit()
    return "database initialized"
