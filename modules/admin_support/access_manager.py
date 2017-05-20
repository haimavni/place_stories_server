from injections import inject
from gluon.storage import Storage
from gluon.utils import simple_hash, web2py_uuid    
import datetime

def encrypt_password(password):
    salt = str(web2py_uuid()).replace('-', '')[-16:]
    digest_alg='pbkdf2(1000,20,sha512)'
    key = None
    h = simple_hash(password, key, salt, digest_alg)
    return '%s$%s$%s' % (digest_alg, salt, h)

def register_new_user(email, password, first_name, last_name, registration_key=''):
    db = inject('db')
    cpassword = encrypt_password(password)
    if not db(db.auth_user.email==email).isempty():
        raise UserError('User "{em}" already exists!'.format(em=email))
    fields = dict(
        email=email,
        first_name=first_name, 
        last_name=last_name, 
        password=cpassword, 
        registration_key=registration_key,
    )
    return db.auth_user.insert(**fields)

class AccessManager:
    db = inject('db')
    user_fields = [
        db.auth_user.id, 
        db.auth_user.email, 
        db.auth_user.first_name,
        db.auth_user.last_name,
        db.auth_user.registration_key,
    ]

    @staticmethod
    def auth_groups():
        db = inject('db')
        groups = db(db.auth_group).select()
        return [g for g in groups if not g.role.startswith('user')]

    def get_groups(self, by_developer):
        db, auth = inject('db', 'auth')
        groups = AccessManager.auth_groups()
        forbidden_group_set = [] if by_developer else set(['DEVELOPER', 'LINGUIST'])
        return [grp for grp in groups if grp.role not in forbidden_group_set]

    def user_data(self, usr, by_developer=False):
        auth = inject('auth')
        result = usr
        roles = []
        for grp in self.get_groups(by_developer):
            role_title = ' '.join([z.capitalize() for z in grp.role.split('_')])
            roles.append(dict(role=grp.role, role_title=role_title, active= auth.has_membership(grp.id, usr.id)))
        result.roles = roles
        result.status = 'Unconfirmed' if result.registration_key else ''        
        return result

    def get_users_data(self):
        db, auth = inject('db', 'auth')
        if auth.user:
            name = (auth.user.first_name + ' ' + auth.user.last_name).lower()
            by_developer = name in ('haim avni', 'barak shohat')
        else:
            by_developer = False
        result = []
        lst = db(db.auth_user).select(*AccessManager.user_fields)
        for usr in lst:
            data = self.user_data(usr, by_developer)
            result.append(data)
        return result

    def modify_membership(self, usr_id, grp_id, on):
        auth = inject('auth')
        if on:
            auth.add_membership(grp_id, usr_id)
        else:
            auth.del_membership(grp_id, usr_id)

    def add_or_update_user(self, user_data):
        db, auth, User_Error = inject('db', 'auth', 'User_Error')
        new_user = not user_data.id
        if not (user_data.last_name and user_data.first_name and user_data.email):
            raise User_Error('All fields are mandatory!')
        if new_user and not user_data.password:
            raise User_Error('A password must be entered!')
        if 0 < len(user_data.password or '') < 4:
            raise User_Error('Password is too short!')
        if new_user:
            cond = True
        else:
            cond = user_data.email != db(db.auth_user.id==user_data.id).select().first().email
        if cond and not db(db.auth_user.email==user_data.email).isempty():
            raise User_Error('User "{em}" already exists!'.format(em=user_data.email))
        if new_user:
            uid = register_new_user(user_data.email, 
                                    user_data.password, 
                                    user_data.first_name, 
                                    user_data.last_name, 
                                    registration_key=user_data.registration_key,
                                    )
            usr = db(db.auth_user.id==uid).select().first()
        else:
            uid = int(user_data.id)
            updated_data = dict(first_name=user_data.first_name, 
                                last_name=user_data.last_name, 
                                email=user_data.email,
                                registration_key=None)
            if user_data.password:
                cpassword = encrypt_password(user_data.password)
                updated_data['password'] = cpassword
            db(db.auth_user.id==uid).update(**updated_data)
            usr = db(db.auth_user.id==uid).select().first()

        usr = db(db.auth_user.id==uid).select(*AccessManager.user_fields).first()
        user_data = self.user_data(usr)
        return user_data, new_user

    def delete_user(self, uid):
        db = inject('db')
        n = db(db.auth_user.id==uid).delete()

mask = 1 << 40 | 1 << 38 | 1 << 21 | 1 << 19
def shift(seed):
    lsb = seed & 1
    seed >>= 1
    if lsb:
        seed ^= mask
    return seed
