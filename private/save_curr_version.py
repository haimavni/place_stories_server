import datetime

s = str(datetime.datetime.now())[:16]

env = '''
export default {{
    debug: false,
    testing: false,
    baseURL: '',
    version: '{}'
}};
'''.format(s) 

with open('aurelia_project/environments/tmp_env.ts', mode='w') as f:
    f.write(env)
    
with open('/home/haim/curr_version.txt', 'w') as f:
    f.write(s)
