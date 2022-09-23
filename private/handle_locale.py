import os
import zlib
from distutils import dir_util
from shutil import copyfile
import datetime
'''
Create temporary environment file for Aurelia to ensure dictionaries are not cached
'''

def to_bytes(obj, charset="utf-8", errors="strict"):
    if obj is None:
        return None
    if isinstance(obj, (bytes, bytearray)):
        return bytes(obj)
    if isinstance(obj, str):
        return obj.encode(charset, errors)
    raise TypeError("Expected bytes")

os.chdir("/home/haim/client_src")
cwd = os.getcwd()
print(("cwd: ", cwd))
dic = dict()
combined_crc = 0xffffffff
for root, dirs, files in os.walk(cwd + '/locales', topdown=True):
    for file in files:
        if not file.endswith('.json'):
            continue
        print((root, file))
        fname = root + '/' + file
        with open(fname, 'r') as f:
            blob = f.read()
        file_name, ext = os.path.splitext(file)
        r = root.find('locales')
        tail = root[r:]
        blob = to_bytes(blob)
        crc = zlib.crc32(blob)
        combined_crc ^= crc
        dic[tail] = dict(source=fname, target='/home/haim/deployment_folder/' + tail + '/' + file_name)
for k in dic:
    target = dic[k]['target'] + '{:0x}'.format(combined_crc & 0xffffffff) + ext
    source = dic[k]['source']
    target_path, f = os.path.split(target)
    dir_util.mkpath(target_path)
    copyfile(source, target)
    
s = str(datetime.datetime.now())[:16]

with open('/home/haim/curr_version.tmp', 'w') as f:
    f.write(s)
    
env = f'''
export default {{
    debug: false,
    testing: false,
    baseURL: '',
    version: '{s}',
    app: '',
    i18n_ver: '{combined_crc & 0xffffffff:0x}'
}};
''' 

with open('/home/haim/client_src/aurelia_project/environments/tmp_env.ts', mode='w') as f:
    f.write(env)
