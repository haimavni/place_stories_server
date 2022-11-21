from gluon.scheduler import Scheduler
import datetime
import ws_messaging
from help_support import update_help_messages, update_letter_templates
from create_app import create_pending_apps
from words import update_word_index_all
from members_support import set_story_sorting_keys
from docs_support import calc_doc_stories
import os
from topics_support import fix_is_tagged
from folders import safe_open
from send_email import email
from video_support import calc_missing_youtube_info
from health import check_health

def test_scheduler(msg):
    comment("test task {}", msg)

class MyScheduler(Scheduler):
    
    def __init__(self, db, tasks, one_time_tasks):
        Scheduler.__init__(self, db, tasks)
        self.one_time_tasks = one_time_tasks

    def restart_task(self, task_id, period=None):
        self.stop_task(task_id)
        now = datetime.datetime.now()
        args = dict(status='QUEUED',
                    start_time=now, ### + timedelta(seconds=10),
                    next_run_time=now, ### + timedelta(seconds=10),
                    enabled=True,
                    stop_time=now + datetime.timedelta(days=1461))
        if period:
            args['period'] = period
        db = self.db
        db(db.scheduler_task.id==task_id).update(**args)
        args['start_time'] = str(args['start_time'])[:19]
        args['next_run_time'] = str(args['next_run_time'])[:19]
        args['stop_time'] = str(args['stop_time'])[:19]
        ws_messaging.send_message(key='task_status_changed', group='TASK_MONITOR', task_id=task_id, data=args)
        return task_id

    def on_update_task_status(self, task_id, data):
        ##comment("task {} status changed: {} ", task_id, data)
        try:
            ###comment("task {task_id} status changed {data}", task_id=task_id, data=data)
            ws_messaging.send_message(key='task_status_changed', group='TASK_MONITOR', task_id=task_id, data=data)
        except Exception as e:
            log_exception('failed broadcasting update task status')

def secs_to_dhms(t):
    s = t % 60
    t /= 60
    m = t % 60
    t /=  60
    h = t % 60
    t /= 60
    d = t / 24
    return d, h, m, s

def plural(t):
    return 's' if t != 1 else ''

def t_unit_str(unit, t):
    return '{t} {u}{p} '.format(t=t, u=unit, p=plural(t)) if t else ''

def time_dif_str(tim, now = datetime.datetime.now()):
    ago = now > tim
    dif = now - tim if ago else tim - now
    dif = int(dif.total_seconds())
    d, h, m, s = secs_to_dhms(dif)
    difstr = t_unit_str('day', d) + t_unit_str('hour', h) + t_unit_str('minute', m) + t_unit_str('second', s)
    return difstr + ' ago' if ago else 'in ' + difstr

def watchdog():
    q = (db.scheduler_task.status.belongs(['FAILED', 'TIMEOUT']))
    tsk = db(q).select().first() 
    if not tsk:
        return
    tsks = db(q).select()
    tsks = [tsk.function_name for tsk in tsks]
    tsks_str = ', '.join(tsks)
    message = '''
    Task(s) {tsks} of {app} {status} in the scheduler. Check the log files.
    '''.format(tsks=tsks_str, app=request.application, status=tsk.status)
    email(sender="admin", to="haimavni@gmail.com", subject = "A task failed", message=message)
    for tsk in db(q).select():
        comment('Task {t} failed', t=tsk.function_name)
    db(q).update(status='QUEUED')
    db.commit()
    
def dict_to_json_str(dic):
    return response.json(dic)

def execute_task(*args, **vars):
    comment("entered execute task")
    try:
        name = vars['name']
        command = vars['command']
        comment('Started task {}: {}'.format(name, command))
        function = scheduler.one_time_tasks[command]
    except Exception as e:
        log_exception('error enter execute task ')
        raise
    try:

        result = function()
    except Exception as e:
        log_exception('Error executing ' + name)
    else:
        comment('Finished task {}. Returned {}.'.format(name, result))
        db.commit()

def schedule_background_task(name, command, period=None, timeout=None):
    return db.scheduler_task.insert(
        status='QUEUED',
        application_name=request.application,
        task_name = 'Execute ' + name,
        vars = dict_to_json_str(dict(name=name, command=command)),
        function_name='execute_task',
        start_time=request.now,
        stop_time=request.now + datetime.timedelta(days=1461),
        repeats=1,
        period=period or (6 * 60 * 60), #6 hours
        timeout=timeout or (60 * 60),   #at most one hour
    )

def schedule_update_help_messages():
    now = datetime.datetime.now()
    return db.scheduler_task.insert(
        status='QUEUED',
        application_name=request.application,
        task_name = 'update help messages',
        function_name='update_help_messages',
        start_time=now,
        stop_time=now + datetime.timedelta(days=1461),
        repeats=0,
        period=3600,   # every hour
        timeout=5 * 60 , # will time out if running for 5 minutes
    )

def schedule_check_health():
    now = datetime.datetime.now()
    return db.scheduler_task.insert(
        status='QUEUED',
        application_name=request.application,
        task_name='check database integrity',
        function_name='check_health',
        start_time=now,
        stop_time=now + datetime.timedelta(days=1461),
        repeats=0,
        period=3600,   # every hour
        timeout=5 * 60 , # will time out if running for 5 minutes
    )

def schedule_calc_missing_youtube_info():
    now = datetime.datetime.now()
    return db.scheduler_task.insert(
        status='QUEUED',
        application_name=request.application,
        task_name = 'calc missing youtube info',
        function_name='calc_missing_youtube_info',
        start_time=now,
        stop_time=now + datetime.timedelta(days=1461),
        repeats=0,
        period=360,   # every three minutes
        timeout=5 * 60 , # will time out if running for 5 minutes
    )


def schedule_update_letter_templates():
    now = datetime.datetime.now()
    return db.scheduler_task.insert(
        status='QUEUED',
        application_name=request.application,
        task_name = 'update letter templates',
        function_name='update_letter_templates',
        start_time=now,
        stop_time=now + datetime.timedelta(days=1461),
        repeats=0,
        period=3600,   # every hour
        timeout=5 * 60 , # will time out if running for 5 minutes
    )

def schedule_watchdog():
    now = datetime.datetime.now()
    return db.scheduler_task.insert(
        status='QUEUED',
        application_name=request.application,
        task_name = 'tasks watchdog',
        function_name='watchdog',
        start_time=now,
        stop_time=now + datetime.timedelta(days=1461),
        repeats=0,
        period=3 * 60,   # every 3 minutes
        timeout=2 * 60 , # will time out if running for 2 minutes
    )

def schedule_update_word_index_all():
    now = datetime.datetime.now()
    return db.scheduler_task.insert(
        status='QUEUED',
        application_name=request.application,
        task_name = 'update word index all',
        function_name='update_word_index_all',
        start_time=now,
        stop_time=now + datetime.timedelta(days=1461),
        repeats=0,
        period=180,   # 3 minutes
        timeout = 600, # will time out if running for 10 minutes
    )

def schedule_set_story_sorting_keys():
    now = datetime.datetime.now()
    return db.scheduler_task.insert(
        status='QUEUED',
        application_name=request.application,
        task_name = 'set_story_sorting_keys',
        function_name='set_story_sorting_keys',
        start_time=now,
        stop_time=now + datetime.timedelta(days=1461),
        repeats=0,
        period=1800,   # half an hour
        timeout = 600, # will time out if running for 10 minutes
    )
  

def schedule_calc_doc_stories():
    now = datetime.datetime.now()
    return db.scheduler_task.insert(
        status='QUEUED',
        application_name=request.application,
        task_name = 'calc doc stories',
        function_name='calc_doc_stories',
        start_time=now,
        stop_time=now + datetime.timedelta(days=1461),
        repeats=0,
        period=600,   # every 10 minutes
        timeout = 500, # will time out if running for 500 seconds
    )

def schedule_create_pending_apps():
    now = datetime.datetime.now()
    return db.scheduler_task.insert(
        status='QUEUED',
        application_name=request.application,
        task_name = 'create pending apps',
        function_name='create_pending_apps',
        start_time=now,
        stop_time=now + datetime.timedelta(days=1461),
        repeats=0,
        period=600,   # every 10 minutes
        timeout = 300, # will time out if running for 500 seconds
    )

permanent_tasks = dict(
    #note that the key must also be function_name set by the keyed item
    watch_dog=schedule_watchdog,
    update_word_index_all=schedule_update_word_index_all,
    set_story_sorting_keys=schedule_set_story_sorting_keys,
    calc_missing_youtube_info=schedule_calc_missing_youtube_info,
    calc_doc_stories=schedule_calc_doc_stories,
    create_pending_apps=schedule_create_pending_apps,
    update_help_messages=schedule_update_help_messages,
    check_health=schedule_check_health,
    update_letter_templates=schedule_update_letter_templates
)

__tasks = dict(
    watchdog=watchdog,
    update_word_index_all=update_word_index_all,
    set_story_sorting_keys=set_story_sorting_keys,
    calc_missing_youtube_info=calc_missing_youtube_info,
    calc_doc_stories=calc_doc_stories,
    create_pending_apps=create_pending_apps,
    execute_task=execute_task,
    update_help_messages=update_help_messages,
    check_health=check_health,
    update_letter_templates=update_letter_templates
)

__one_time_tasks = dict(
    fix_is_tagged=fix_is_tagged
)

scheduler = MyScheduler(db, __tasks, __one_time_tasks)

def verify_tasks_started():
    if db(db.auth_user).count() < 2:
        return
    lock_file_name = '{p}tasks[{a}].lock'.format(p=log_path(), a=request.application)
    if db(db.scheduler_task).isempty() and os.path.isfile(lock_file_name):
        os.remove(lock_file_name)
    if os.path.isfile(lock_file_name):
        return
    with safe_open(lock_file_name, 'w') as f:
        f.write('locked')
    for function_name in permanent_tasks:
        ###if db(db.scheduler_task.function_name==function_name).isempty():
        task_id = permanent_tasks[function_name]()
        comment("start {}, task_id is {}", function_name, task_id)
        db.commit()
        
def promote_task(function_name):
    tsk = db(db.scheduler_task.function_name==function_name).select().first()
    if tsk:
        if tsk.status in ['ASSIGNED', 'RUNNING']:
            return
        tsk.update_record(status='QUEUED', next_run_time=datetime.datetime.now())
    elif function_name in permanent_tasks:
        func = permanent_tasks[function_name]
        func()

verify_tasks_started()       