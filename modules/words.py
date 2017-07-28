# coding: utf8

import re
from bs4 import BeautifulSoup

alef = "א"
tav = "ת"

word_pat = r'([{alef}-{tav}]+|[0-9./]+|[a-zA-Z]+)'.format(alef=alef, tav=tav)
word_regex = re.compile(word_pat, re.UNICODE | re.MULTILINE)

def remove_all_tags(html):
    soup = BeautifulSoup(html)
    text = soup.get_text()
    return text

def extract_words(s):
    s = remove_all_tags(s)
    ###lst = word_regex.findall(s, re.UNICODE | re.MULTILINE)
    return re.split(r'\s+', s)



