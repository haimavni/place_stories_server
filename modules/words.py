# coding: utf8

import re
from bs4 import BeautifulSoup
from guess_language import guessLanguage as guess
from langs import extract_words

alef = "א"
tav = "ת"

word_pat = r'([{alef}-{tav}]+|[0-9./]+|[a-zA-Z]+)'.format(alef=alef, tav=tav)
word_regex = re.compile(word_pat, re.UNICODE | re.MULTILINE)

def remove_all_tags(html):
    soup = BeautifulSoup(html)
    text = soup.get_text()
    return text

def extract_tokens(s):
    s = remove_all_tags(s)
    ###lst = word_regex.findall(s, re.UNICODE | re.MULTILINE)
    return re.split(r'\s+', s)

def guess_language(html):
    s = remove_all_tags(html)
    return guess(s)

def tally_words(html, dic, story_id):
    s = remove_all_tags(html)
    lst = extract_words(s)
    for w in lst:
        if w not in dic:
            dic[w] = {}
        if story_id not in dic[w]:
            dic[w][story_id] = 0
        dic[w][story_id] += 1
    x = len(dic)

def tally_all_stories():   
    from injections import inject
    db = inject('db')
    dic = {}
    for rec in db(db.TblStories).select():
        html = rec.story
        tally_words(html, dic, rec.id)
    for w in dic:
        print '{}: {}'.format(w, len(dic[w]))
    x = len(dic)

    
def test():
    html = 'חיים אבני כותב תוכנית מחשב computer program'
    tally_words
    
if __name__ == '__main__'    :
    test()
    



