import os
import zlib
from shutil import copyfile

os.chdir("/home/haim/aurelia-gbs/gbs")
cwd = os.getcwd()
print "cwd: ", cwd
dic = dict()
combined_crc = 0xffffffff
for root, dirs, files in os.walk(cwd + '/locales', topdown=True):
    for file in files:
        if not file.endswith('.json'):
            continue
        print root, file
        fname = root + '/' + file
        with open(fname, 'r') as f:
            blob = f.read()
        file_name, ext = os.path.splitext(file)
        r = root.find('locales')
        tail = root[r:]
        crc = zlib.crc32(blob)
        combined_crc ^= crc
        dic[tail] = dict(source=fname, target='/home/haim/deployment_folder/' + tail + '/' + file_name)
for k in dic:
    target = dic[k]['target'] + '{:0x}'.format(combined_crc & 0xffffffff) + ext
    source = dic[k]['source']
    copyfile(source, target)
    
env = '''
export default {{
    debug: false,
    testing: false,
    baseURL: '',
    i18n_ver: '{:0x}'
}};
'''.format(combined_crc & 0xffffffff) 

with open('aurelia_project/environments/tmp_env', mode='w') as f:
    f.write(env)
        
    
        
