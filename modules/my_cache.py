from .injections import inject
from gluon.contrib.memcache import memcache
import re

valid_key_chars_re = re.compile('[\x21-\x7e\x80-\xff]+$')

class Cache:

    def __init__(self, name, *args, **kargs):
        self.mc = memcache.Client(['localhost:11211'])
        key = Cache.make_key(name, *args, **kargs)
        self.key = Cache.fix_key(key)

    @staticmethod
    def make_key(name, *args, **kargs):
        result = name.__name__ if callable(name) else name
        args = [str(a) for a in args]
        s = '-'.join(args)
        if s:
            result += '-' + s
        lst = [k + '-' + str(v) for k, v in list(kargs.items())]
        s = '-'.join(lst)
        if s:
            result += '-' + s
        return result

    @staticmethod
    def fix_key(key):
        #prefix with server id and convert to hex if key contains control characters
        request = inject('request')
        s = request.env.http_host
        if '.' in s:
            prefix = s.split('.')[0] + '-'
            if prefix == '127-':  #just for the development PC
                prefix = ''
        else:
            prefix = ''
        prefix += request.application + '-'
        key = prefix + key
        if not valid_key_chars_re.match(key):
            key = key.encode('hex')
        return key

    @staticmethod
    def cache_key_list():
        mc = memcache.Client(['localhost:11211'])
        k = Cache.fix_key('all_cached_keys')
        return mc.get(k)

    def update_key_list(self, delete=False):
        #maintain list of all keys - did not find mc method that does it...
        k = Cache.fix_key('all_cached_keys') 
        key_list = self.mc.get(k) or set([])
        if delete:
            if self.key in key_list:
                key_list -= set([self.key])
        elif self.key not in key_list:
            key_list |= set([self.key])
        self.mc.set(k, key_list)
        check_list = self.mc.get(k)
        if check_list != key_list:
            comment = inject('comment')
            comment("update key list failed!")
            ##raise Exception('update key list failed!')

    def __call__(self, func=None, refresh=False, time_expire=0):
        result = None if refresh else self.mc.get(self.key)
        if func and not result:
            result = func() if callable(func) else func
            self.mc.set(self.key, result, time=time_expire)
            self.update_key_list()
        return result

    def update(self, func=None): 
        result = self.mc.get(self.key)
        func(result)
        #self.mc.set(self.key, result) #It would defeat the performance gain!. func needs to store
        return result                  #the change so next load will have it  

    def delete(self):
        self.mc.delete(self.key)
        self.update_key_list(delete=True)