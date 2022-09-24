import os
import glob
import sys

os.chdir("/home/haim/client_src")

def write_index_html():
    p = '/home/haim/deployment_folder/scripts/vendor-bundle-'
    lst = glob.glob(p + '*.js')
    vname = lst[0]
    version = vname[len(p):]
    branch = sys.args[1]
    base = f'https://tol.life/tol_{branch}/static/aurelia/'
    left_curl = '{'
    right_curl = '}'
    index_html = f'''
<!DOCTYPE html>
<html>

<head>
    <meta charset="utf-8">
    <meta http-equiv="expires" content="0">
    <meta name="google-site-verification" content="JnVD2e5l285fDPinK4jNDMeZ19eZs1Rx5WRLajzCxs8" />
    <link rel="shortcut icon" href="/favicon.ico" type="image/x-icon">

    <title>Stories</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="google-site-verification" content="HWlQ64YZv4Qp97_JanEUUJl58eED5bcUjA3RPSL13Dk" />
    <link rel="stylesheet" href="/fontawesome/css/all.css" type="text/css" />
    <base href={base}>
</head>

<body aurelia-app="main">
    <script>
        CheckUrl("/scripts/vendor-bundle-{version}.js");
        async function CheckUrl(url)
        {left_curl}
            const response = await fetch(url, {left_curl}
            method: "head",
            mode: "no-cors"
            {right_curl});
            if (response.status == 404) {left_curl}
                //alert("Please refresh");
                location.reload(true);
            {right_curl}
        {right_curl}
    </script>
    <script src="/scripts/vendor-bundle-{version}.js" data-main="aurelia-bootstrapper" ></script>
</body>

</html>
'''
    with open('/home/haim/deployment_folder/index.html', 'w', encoding="utf-8") as f:
        f.write(index_html)
    with open(vname, 'r', encoding="utf-8") as f:
        txt = f.read()
    txt = txt.replace('../scripts/app', base  + 'scripts/app')
    with open(vname, 'w', encoding="utf-8") as f:
        f.write(txt)



# with open('index.html') as f:
#     s = f.read()
#     pat = r'<script src=\"scripts/vendor-bundle-(.*?)\.js\"'
#     m = re.search(pat, s)
#     version = m.group(1)
#     s = s.replace('[VERSION]', version)
#     print(f"version {version} copied")
    
# with open('index.html', 'w') as g:
#     g.write(s)
write_index_html()