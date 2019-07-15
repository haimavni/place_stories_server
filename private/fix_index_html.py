import os
import re

os.chdir("/home/haim/aurelia-gbs/gbs")


with open('index.html') as f:
    s = f.read()
    pat = r'<script src=\"scripts/vendor-bundle-(.*?)\.js\"'
    m = re.search(pat, s)
    version = m.group(1)
    s = s.replace('[VERSION]', version)
    
with open('index.html', 'w') as g:
    g.write(s)
