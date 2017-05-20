fmt_css = '''    <link rel="stylesheet" href="{{!= URL(c='static/lib', f='{}') !}}" />'''
fmt_js = '''    <script type="text/javascript" src="{{!= URL(c='static/lib', f='{}') !}}"></script>'''

file_list_name = 'bower_list.txt'
with open('bower_list.html', mode='w') as out:
    with open(file_list_name) as f:
        for fname in f:
            fname = fname.strip()
            if fname.endswith('css'):
                fmt = fmt_css
            elif fname.endswith('js'):
                fmt = fmt_js
            else:
                continue
            s = fmt.format(fname)
            out.write(s + '\n')
            