import base64

with open('/home/haim/aurelia-gbs/server/tol_server/private/ssl-certificate/bundle-zip.txt') as f:
    text = f.read()
text = text.replace('\n', '')
    
blob = base64.b64decode(text)

with open('bundle.zip', 'wb') as f:
    f.write(blob)

