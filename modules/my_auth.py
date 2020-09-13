from gluon.tools import Auth
from gluon.validators import *
from gluon.utils import web2py_uuid
from gluon.dal import Row
from gluon.storage import Storage
from injections import inject
from admin_support.access_manager import AccessManager

class MyAuth(Auth):

    def change_password(self, old_password, new_password, uid=None):
        from admin_support.access_manager import encrypt_password
        db = self.db
        curr_password = db(db.auth_user.id==uid).select(db.auth_user.password).first().password
        if curr_password != encrypt_password(old_password):
            return False
        p = encrypt_password(new_password)
        db(db.auth_user.id==uid).update(password=p)
        return True

    def all_groups(self):
        lst = self.db(self.settings.table_group.id > 0).select()
        return lst

    def all_users(self):
        lst = self.db(self.settings.table_user.id > 0).select()
        return lst

    def set_access_manager(self, ACCESS_MANAGER, id):
        if not self.has_membership(ACCESS_MANAGER, id):
            self.add_membership(ACCESS_MANAGER, id)

    def current_user(self):
        #use session.current_user to fake another user
        session, request = inject('session', 'request')
        if self.user:
            return session.current_user or self.user.id
        if request.env.server_name == 'haim-VirtualBox':
            return 2
        return None
    
    def user_id_of_email(self, email, name=None):
        db = self.db
        rec = db(db.auth_user.email==email).select(db.auth_user.id).first()
        user_id = rec.id if rec else None
        #if create_if_not_exist:
        #    self.register...
        return user_id
    
    def resend_verification_email(self, uid):
        db = self.db
        user_rec = db(db.auth_user.id==uid).select().first()
        if not (self.settings.mailer and self.settings.mailer.send(
            to=user_rec.email,
            subject=self.messages.verify_email_subject,
            message=self.messages.verify_email % dict(key=user_rec.registration_key))):
            raise Exception(T('Failed to resend verify email to {}').format(user_rec.email))
        
    def verify_email(self, key):
        """
        Action used to verify the registration email
        """
        EDITOR, PHOTO_UPLOADER = inject('EDITOR', 'PHOTO_UPLOADER')
        table_user = self.table_user()
        user = table_user(registration_key=key)
        if not user:
            return False
        user.update_record(registration_key='')
        self.add_membership(user_id=user.id, group_id=EDITOR)
        self.add_membership(user_id=user.id, group_id=PHOTO_UPLOADER)
        return True
    
    def register_user(self, user_info):
        from gluon.utils import web2py_uuid
        db, User_Error, auth = inject('db', 'User_Error', 'auth')
        u = user_info
        if not db(db.auth_user.email==u.email).isempty():
            raise User_Error('email-already-exists')
        u.registration_key = key = web2py_uuid()
    
        am = AccessManager()
        user, is_new_user = am.add_or_update_user_bare(u)
        #send verification email to new user
        link = auth.url('verify_email', args=[key], scheme=True)
        u.update(dict(key=key, link=link, username=u.email))
        good = auth.settings.mailer and auth.settings.mailer.send(
            to=u.email,
            subject=auth.messages.verify_email_subject,
            message='Click on the link {lnk} to verify your email'.format(lnk=link))
        if not good:
            db.rollback()
            raise User_Error('cant-send-mail')
        self.notify_registration(user_info)
        return user
    
    def notify_registration(self, user_info):
        request, db, mail, ACCESS_MANAGER = inject('request', 'db', 'mail', 'ACCESS_MANAGER')
        app = reqeuest.application
        ui = user_info
        user_name = ui.first_name + ' ' + ui.last_name
        email = ui.email
        lst = db((db.auth_membership.group_id==ACCESS_MANAGER)&(db.auth_user.id==db.auth_membership.user_id)&(db.auth_user.id>1)).select(db.auth_user.email)
        receivers = [r.email for r in lst]    
        message = ('', '''
        {uname} has just registered to <b>GB Stories</b>.
        Email adddress is {uemail}.
    
    
        Click <a href="https://gbstories.org/{app}/static/aurelia/index.html#/access-manager">here</a> for access manager.
        '''.format(uname=user_name, uemail=email, app=app).replace('\n', '<br>'))
        mail.send(to=receivers, subject='New GB Stories registration', message=message)
        
    def user_has_privilege(self, privilege):
        return self.has_membership(privilege, self.current_user())

    def user_language(self, language=None):
        db = self.db
        uid = self.current_user()
        if language:
            db(db.auth_user.id==uid).update(language=language)
            db.commit()
        user_rec = db(db.auth_user.id==uid).select().first()
        return user_rec.language or 'en'
    
    def user_name(self, user_id=None):
        user_id = user_id or (self.user.id if self.user else None)
        if not user_id:
            return ''
        db = self.db
        user = db(db.auth_user.id==user_id).select().first()
        return user.first_name + ' ' + user.last_name
    
    def get_privileges(self):
        if not self.user:
            return
        user_groups = self.user_groups = {}
        table_group = self.table_group()
        table_membership = self.table_membership()
        memberships = self.db(
            table_membership.user_id == self.user.id).select()
        privileges = Storage()
        for membership in memberships:
            group = table_group(membership.group_id)
            if group:
                privileges[group.role] = True
        return privileges
    
    def login_bare(self, username, password, sneak_in=False):
        """
        Logins user as specified by username (or email) and password
        """
        settings = self._get_login_settings()
        user = settings.table_user(**{settings.userfield: username})
        if not user:
            return 'user-not-registered'
        if sneak_in:
            return user
        if user and user.get(settings.passfield, False):
            if user.registration_key:
                return 'incomplete-registration'
            password = settings.table_user[settings.passfield].validate(password)[0]
            if password == user[settings.passfield]:
                self.login_user(user)
                return user
        return 'wrong-password'
    
    def user_list(self):
        db = inject('db')
        lst = db(db.auth_user).select()
        result = dict()
        for u in lst:
            result[u.id] = dict(name = u.first_name + ' ' + u.last_name,
                                email = u.email)
        return result
    
        
        
