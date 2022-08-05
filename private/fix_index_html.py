import os
import re

os.chdir("/home/haim/aurelia")


with open('index.html') as f:
    s = f.read()
    pat = r'<script src=\"scripts/vendor-bundle-(.*?)\.js\"'
    m = re.search(pat, s)
    version = m.group(1)
    s = s.replace('[VERSION]', version)
    print(f"version {version} copied")
    
with open('index.html', 'w') as g:
    g.write(s)
