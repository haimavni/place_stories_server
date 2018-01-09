from scheduler import Scheduler
import datetime
import time
from gluon.storage import Storage
import re
import ws_messaging
from my_cache import Cache
from photos import scan_all_unscanned_photos
from collect_emails import collect_mail
from injections import inject

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
        #comment('on update task status', log_name='dbg_scheduler')
        comment = inject('comment')
        try:
            comment("task {task_id} status changed {data}", task_id=task_id, data=data)
            ws_messaging.send_message(key='task_status_changed', group='TASK_MONITOR', task_id=task_id, data=data)
        except Exception, e:
            log_exception('failed on update task status')

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

def execute_task(name, command):
    comment('Started task {}: {}'.format(name, command))
    try:
        result = eval(command)
    except Exception, e:
        log_exception('Executing ' + name)
    else:
        comment('Finished task {}. Returned {}.'.format(name, result))
        db.commit()

__tasks = dict(
    ###scan_all_unscanned_photos=scan_all_unscanned_photos,
    collect_mail=collect_mail,
    execute_task=execute_task,
)

def dict_to_json_str(dic):
    return response.json(dic)

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
        timeout = 5 * 60, # will time out if running for a 5 minutes
    )

scheduler = MyScheduler(db, __tasks)

permanent_tasks = dict(
    ##scan_all_unscanned_photos=schedule_scan_all_unscanned_photos
    #look for emailed photos and other mail
    collect_mail=schedule_collect_mail
)

def _verify_tasks_started():
    
    if db(db.auth_user).count() < 2:
        return
    comment = inject('comment')
    comment("verify tasks started")
    for task_name in permanent_tasks:
        comment("start {}", task_name)
        if db(db.scheduler_task.task_name==task_name).isempty():
            permanent_tasks[task_name]()
    comment('tasks verified.')
    return True

def verify_tasks_started():
    #do NOT use memcache - it must be run once when the server starts. The memcache is NOT deleted at that time, 
    #so the verification may never be called
    c = Cache('VERIFY_TASKS_STARTED')
    return c(lambda: _verify_tasks_started())

verify_tasks_started()       