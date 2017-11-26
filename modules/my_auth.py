from gluon.tools import Auth
from gluon.validators import *
from gluon.utils import web2py_uuid
from gluon.dal import Row
from gluon.storage import Storage
from injections import inject

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
        session = inject('session')
        if self.user:
            return session.current_user or self.user.id
        return None

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
    
    def login_bare(self, username, password):
        """
        Logins user as specified by username (or email) and password
        """
        settings = self._get_login_settings()
        user = settings.table_user(**{settings.userfield: username})
        if not user:
            return 'user-not-registered'
        if user and user.get(settings.passfield, False):
            if user.registration_key:
                return 'incomplete-registration'
            password = settings.table_user[settings.passfield].validate(password)[0]
            if password == user[settings.passfield]:
                self.login_user(user)
                return user
        return 'wrong-password'
    
    
        
        
