# coding: utf-8

import re
from selectolax.parser import HTMLParser

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

def replace_nbsps(s):
    return s.replace('&nbsp;', '&#9899;')

def remove_special_chars(s):
    return s.replace("“", '"')

def clean_html(html, nbsp_too=True):
    html = remove_style_defs(html)
    html = replace_divs(html)
    html = remove_special_chars(html)
    if nbsp_too:
        html = replace_nbsps(html)
        ###html = html.replace("&nbsp;", "")
    return html

def unlink_all(html):
    pat_str = r'<a.*?>(.*?)</a>'
    pat = re.compile(pat_str, re.IGNORECASE)
    result = pat.sub(replace_a, html)
    return result

def replace_a(m):
    return m.group(1)

def html_to_text(html):
    tree = HTMLParser(html)

    if tree.body is None:
        return None

    for tag in tree.css('script'):
        tag.decompose()
    for tag in tree.css('style'):
        tag.decompose()

    text = tree.body.text(separator='\n')
    return text


