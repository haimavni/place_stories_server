import re

def clean_dirt(m):
    return ""

def remove_style_defs(s):
    pat_str = r'''(style=".+?")|(style='.+?')|(<font.+?>)|(</font>)|(class=".+?")|(lang=".+?")|(align=".+?")|(dir=".+?")'''
    pat = re.compile(pat_str, re.IGNORECASE)
    result = pat.sub(clean_dirt, s)
    return result

def replace_div(m):
    s = m.group(0)
    s = s.replace("div", "p")
    return s

def replace_divs(s):
    pat_str = r'(<div\s*>)|(</div\s*>)'
    pat = re.compile(pat_str, re.IGNORECASE)
    result = pat.sub(replace_div, s)
    return result

def replace_nbsp(m):
    return '<i class="fa fa-square"></i>'

def replace_nbsps(s):
    ##pat_str = r'&nbsp;(\s*&nbsp;)+'
    pat_str = r'&nbsp;(\s*&nbsp;)+'
    pat = re.compile(pat_str)
    result = pat.sub(replace_nbsp, s)
    return result

def clean_html(html, nbsp_too=True):
    html = remove_style_defs(html)
    html = replace_divs(html)
    if nbsp_too:
        html = replace_nbsps(html)
        ###html = html.replace("&nbsp;", "")
    return html
