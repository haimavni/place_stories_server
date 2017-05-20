from injections import inject

class TaskMonitor:

    def search_tasks(self):
        ADMIN, db, auth = inject('ADMIN', 'db', 'auth')
        if auth.has_membership(ADMIN):
            q = (db.auth_user.id > 0) & (db.search_table.owner==db.auth_user.id)
        else:
            q = (db.auth_user.id == auth.ultimate_user()) & (db.search_table.owner==db.auth_user.id)
        q &= (db.search_table.task_id==db.scheduler_task.id)
        result = db(q).select(
            db.auth_user.id,
            db.auth_user.email,
            db.scheduler_task.id,
            db.search_table.name,
            db.scheduler_task.status,
            db.scheduler_task.start_time,
            db.scheduler_task.last_run_time,
            db.scheduler_task.next_run_time,
            db.scheduler_task.times_run,
            db.scheduler_task.times_failed,
            orderby=~db.scheduler_task.last_run_time)
        return result

    def system_tasks(self):
        db, permanent_tasks = inject('db', 'permanent_tasks')
        task_titles = dict(update_all_mood_counts='Update Scores',
                           send_email_notifications='Send Email Notifications',
                           notify_expired_authorization='Notify Expired Authorization',
                           collect_word_statistics='Collect Word Statistics',
                           update_people_profiles='Update People Profiles'
                           )
        result = []
        for task_name in permanent_tasks: 
            rec = db(db.scheduler_task.task_name==task_name).select(
                db.scheduler_task.id,
                db.scheduler_task.status,
                db.scheduler_task.start_time,
                db.scheduler_task.last_run_time,
                db.scheduler_task.next_run_time,
                db.scheduler_task.times_run,
                db.scheduler_task.times_failed,
                orderby=~db.scheduler_task.last_run_time).first()
            rec.task_title = task_titles.get(task_name, task_name.replace('_', ' ').capitalize())
            result.append(rec)
        return result

    def one_time_tasks(self):
        db = inject('db')
        lst = db(db.scheduler_task.task_name.like('Execute%')).select(
            db.scheduler_task.id,
            db.scheduler_task.task_name,
            db.scheduler_task.status,
            db.scheduler_task.start_time,
            db.scheduler_task.last_run_time,
            db.scheduler_task.next_run_time,
            db.scheduler_task.times_run,
            db.scheduler_task.times_failed,
            orderby=~db.scheduler_task.last_run_time
        )
        return lst

    def all_tasks(self):
        ADMIN, auth = inject('ADMIN', 'auth')
        result = []
        for tsk in self.search_tasks():
            rec = dict(
                task_id=tsk.scheduler_task.id,
                user=tsk.auth_user.email,
                name=tsk.search_table.name,
                status=tsk.scheduler_task.status,
                start_time=tsk.scheduler_task.start_time, 
                last_run_time=tsk.scheduler_task.last_run_time, 
                next_run_time=tsk.scheduler_task.next_run_time, 
                times_run=tsk.scheduler_task.times_run, 
                times_failed=tsk.scheduler_task.times_failed
            )
            result.append(rec)
        if not auth.has_membership(ADMIN):
            return result
        for tsk in self.system_tasks():
            rec = dict(
                task_id=tsk.id,
                user='System',
                name=tsk.task_title,
                status=tsk.status,
                start_time=tsk.start_time, 
                last_run_time=tsk.last_run_time, 
                next_run_time=tsk.next_run_time, 
                times_run=tsk.times_run, 
                times_failed=tsk.times_failed
            )
            result.append(rec)
        for tsk in self.one_time_tasks():
            rec = dict(
                task_id=tsk.id,
                user='One time task',
                name=tsk.task_name,
                status=tsk.status,
                start_time=tsk.start_time, 
                last_run_time=tsk.last_run_time, 
                next_run_time=tsk.next_run_time, 
                times_run=tsk.times_run, 
                times_failed=tsk.times_failed,
                deletable=tsk.status=='COMPLETED' or (tsk.status=='FAILED' and tsk.task_name.startswith('Execute'))
            )
            result.append(rec)
        return result

    def restart_task(self, task_id):
        scheduler = inject('scheduler')
        scheduler.restart_task(int(task_id))

    def stop_task(self, task_id):
        scheduler = inject('scheduler')
        return scheduler.stop_task(int(task_id))

    def delete_task(self, task_id):
        db = inject('db')
        n = db(db.scheduler_task.id==task_id).delete()
        return dict(deleted=n==1)
    
    def remove_completed_tasks(self):
        db = inject('db')
        q = (db.scheduler_task.status=='COMPLETED')
        n = db(q).delete()
        return dict(deleted=n)
        