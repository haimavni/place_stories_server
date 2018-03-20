from shutil import move
import os
import random
import string

#shorted bundle name to work around a mysterious cache bug
def random_string():
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(6))

path = "/home/haim/deployment_folder/"
lst = os.listdir(path + 'scripts')
vprefix = random_string()
aprefix = random_string()

for fname in lst:
    if fname.startswith('app'):
        ab_name = fname
        new_ab_name = aprefix + 'ab-' + ab_name.split('-')[-1]
    elif fname.startswith('vendor'):
        vb_name = fname
        new_vb_name = vprefix + 'vb-' + vb_name.split('-')[-1]
    #to enable debugging:
    elif fname.startswith('vb'):
        new_vb_name = fname
        vb_name = None
    elif fname.startswith('ab'):
        new_ab_name = fname
        ab_name = None
if vb_name:
    move(path + 'scripts/' + vb_name, path + 'scripts/' + new_vb_name)
if ab_name:
    move(path + 'scripts/' + ab_name, path + 'scripts/' + new_ab_name)
if vb_name:
    with open(path + 'index.html') as f:
        s = f.read()
    s = s.replace(vb_name, new_vb_name)
    with open(path + 'index.html', 'w') as f:
        f.write(s)
vb = path + 'scripts/' + new_vb_name
with open(vb) as f:
    s = f.read()
if not ab_name:
    ab_name = 'app-bundle-' + new_ab_name.split('-')[-1]
ab_name = ab_name[:-3]
new_ab_name = new_ab_name[:-3]
s = s.replace(ab_name, new_ab_name)
with open(vb, 'w') as f:
    f.write(s)

        
        
    