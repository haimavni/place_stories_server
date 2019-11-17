from admin_support.access_manager import register_new_user, AccessManager
from gluon.utils import web2py_uuid

def init_database():
    if len(request.args) < 4:
        return "database initialized without admin"
    email,password,first_name,last_name = request.args
    usr_id = register_new_user(email, password, first_name, last_name)
    am = AccessManager()
    am.enable_all_roles(usr_id)
    db.commit()
    return "database initialized"

@serve_json
def request_new_app(vars):
    #todo: check uniqueness first
    if not db(db.TblCustomers.app_name==vars.app_name).isempty():
        error_message = "admin.duplicate-app-name"
    else:
        db.TblCustomers.insert(
            first_name=vars.first_name,
            last_name=vars.last_name,
            email=vars.email,
            app_name=vars.app_name,
            confirmation_key=web2py_uuid()
        )
        error_message = ""
    return dict(error_message=error_message)

@serve_json
def confirm_new_app(vars):
    customer_rec = db(db.TblCustomers.app_name==vars.app_name)
    if customer_rec.confirmation_key != vars.confirmation_key:
        raise Exception('Confirmation key mismatch')
    customer_rec.update_record(confirmation_key='')
    return dict()