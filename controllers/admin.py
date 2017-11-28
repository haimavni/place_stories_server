from admin_support.access_manager import AccessManager
from admin_support.task_monitor import TaskMonitor
import ws_messaging

#---------------------------------------------------------------------------
# Access Manager
#---------------------------------------------------------------------------

###@auth.requires_login()  #todo: fix it sometime... maybe
def access_manager():
    return dict()

@serve_json
def get_authorized_users(vars):
    am = AccessManager()
    return dict(authorized_users=am.get_users_data())

@serve_json
def toggle_membership(vars):
    am = AccessManager()
    role_name = vars.role
    role = eval(role_name)
    active = vars.active != 'true'
    am.modify_membership(vars.id, role, active)
    ws_messaging.send_message(key='ROLE_CHANGED', user=vars.id, role=role_name, active=active) 
    return dict(id=vars.id, 
                role=vars.role, 
                active=active)

@serve_json
def add_or_update_user(vars):
    am = AccessManager()
    user_data, new_user = am.add_or_update_user(vars)
    return dict(user_data=user_data, 
                new_user=new_user)

@serve_json
def delete_user(vars):
    uid = vars.id
    n = db(db.auth_user.id==uid).delete()
    return dict(id=vars.id, ok=n==1)
#---------------------------------------------------------------------------
# Task Monitor
#---------------------------------------------------------------------------

@auth.requires_login()
def task_monitor():
    return dict(controller='TaskMonitorCtrl')

@serve_json
def read_tasks(vars):
    tm = TaskMonitor()
    logging.disable(logging.DEBUG)
    task_list=tm.all_tasks()
    logging.disable(logging.NOTSET)
    return dict(task_list=tm.all_tasks())

@serve_json
def restart_task(vars):
    tm = TaskMonitor()
    tm.restart_task(vars.task_id)
    return dict()

@serve_json
def stop_task(vars):
    tm = TaskMonitor()
    tm.stop_task(vars.task_id)
    return dict()

@serve_json
def delete_task(vars):
    tm = TaskMonitor()
    tm.delete_task(vars.task_id)
    return dict()

@serve_json
def remove_completed_tasks(vars):
    tm = TaskMonitor()
    tm.remove_completed_tasks()
    return dict()

@serve_json
def resend_verification_email(vars):
    auth.resend_verification_email(vars.user_id)
    return dict()

