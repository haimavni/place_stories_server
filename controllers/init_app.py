from admin_support.access_manager import register_new_user, AccessManager

def init_database():
    email = request.vars.email
    password = request.vars.password
    last_name = request.vars.last_name or 'admin'
    first_name = request.vars.first_name or 'admin'
    usr_id = register_new_user(email, password, first_name, last_name)
    am = AccessManager()
    am.enable_all_roles(usr_id)
    return "database initialized"



