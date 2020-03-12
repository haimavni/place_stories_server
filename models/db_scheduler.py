from scheduler import Scheduler
import datetime
import time
import random
from gluon.storage import Storage
import re
import ws_messaging
from injections import inject
from photos_support import scan_all_unscanned_photos
from collect_emails import collect_mail
from create_app import create_pending_apps
from words import update_word_index_all
from docs_support import calc_doc_stories
import os
from topics_support import fix_is_tagged

def test_scheduler(msg):
    comment("test task {}", msg)

class MyScheduler(Scheduler):

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
        logger.debug("task {} status changed: {} ".format(task_id, data))
        try:
            ###comment("task {task_id} status changed {data}", task_id=task_id, data=data)
            ws_messaging.send_message(key='task_status_changed', group='TASK_MONITOR', task_id=task_id, data=data)
        except Exception, e:
            logger.error('failed broadcasting update task status')

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
    message = '''
    A task of {app} {status} in the scheduler. Check the log files.
    '''.format(app=request.application, status=tsk.status)
    mail.send(sender="admin@gbstories.org", to="haimavni@gmail.com", subject = "A task failed", message=('', message))
    for tsk in db(q).select():
        comment('Task {t} failed', t=tsk.function_name)
    db(q).update(status='QUEUED')
    db.commit()
    
def randomize_story_sampling():
    for story_rec in db(db.TblStories.deleted!= True).select():
        story_rec.update_record(sampling_id=random.randint(1, SAMPLING_SIZE))
    db.commit()

def dict_to_json_str(dic):
    return response.json(dic)

def execute_task(*args, **vars):
    comment("entered execute task")
    try:
        #for key in vars:
            #comment(" vars[{key}]={val}", key, vars[key])
        #comment('Started task {}: {}'.format(args, vars))
        name = vars['name']
        command = vars['command']
        comment('Started task {}: {}'.format(name, command))
    except Exception, e:
        log_exception('enter execute task ')
        raise
    try:
        result = eval(command)
    except Exception, e:
        log_exception('Executing ' + name)
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

def schedule_scan_all_unscanned_photos():
    path = 'applications/' + request.application + '/logs/'
    now = datetime.datetime.now()
    return db.scheduler_task.insert(
        status='QUEUED',
        application_name=request.application,
        task_name = 'scan_all_unscanned_photos',
        function_name='scan_all_unscanned_photos',
        start_time=now,
        stop_time=now + datetime.timedelta(days=1461),
        repeats=0,
        period=1 * 60 * 60,   # every hour
        timeout = 2 * 60*60, # will time out if running for a two hours
    )

def schedule_collect_mail():
    now = datetime.datetime.now()
    return db.scheduler_task.insert(
        status='QUEUED',
        application_name=request.application,
        task_name = 'collect mail',
        function_name='collect_mail',
        start_time=now,
        stop_time=now + datetime.timedelta(days=1461),
        repeats=0,
        period=3 * 60,   # every 3 minutes
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

def schedule_randomize_story_sampling():
    now = datetime.datetime.now()
    return db.scheduler_task.insert(
        status='QUEUED',
        application_name=request.application,
        task_name = 'tasks randomize story sampling',
        function_name='randomize_story_sampling',
        start_time=now,
        stop_time=now + datetime.timedelta(days=1461),
        repeats=0,
        period=3600,   # every hour
        timeout=5 * 60 , # will time out if running for 5 minutes
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
        period=60,   # minute
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
    ##scan_all_unscanned_photos=schedule_scan_all_unscanned_photos
    #look for emailed photos and other mail
    #note that the key must also be function_name set by the keyed item
    watch_dog=schedule_watchdog,
    randomize_story_sampling=schedule_randomize_story_sampling,
    update_word_index_all=schedule_update_word_index_all,
    calc_doc_stories=schedule_calc_doc_stories,
    create_pending_apps=schedule_create_pending_apps
)
maildir = '/home/{}_mailbox/Maildir'.format(request.application)
if os.path.isdir(maildir):
    permanent_tasks['collect_mail'] = schedule_collect_mail

__tasks = dict(
    ###scan_all_unscanned_photos=scan_all_unscanned_photos,
    collect_mail=collect_mail,
    watchdog=watchdog,
    randomize_story_sampling=randomize_story_sampling,
    update_word_index_all=update_word_index_all,
    calc_doc_stories=calc_doc_stories,
    create_pending_apps=create_pending_apps,
    execute_task=execute_task
)

scheduler = MyScheduler(db, __tasks)

def verify_tasks_started():
    if db(db.auth_user).count() < 2:
        return
    lock_file_name = '{p}tasks[{a}].lock'.format(p=log_path(), a=request.application)
    if db(db.scheduler_task).isempty() and os.path.isfile(lock_file_name):
        os.remove(lock_file_name)
    if os.path.isfile(lock_file_name):
        return
    with open(lock_file_name, 'w') as f:
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