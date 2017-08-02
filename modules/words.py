# coding: utf8

import re
from bs4 import BeautifulSoup
from guess_language import guessLanguage as guess
from langs import extract_words, language_name
from my_cache import Cache
from injections import inject
#from base64 import b64decode, b64encode
from math import log

alef = "א"
tav = "ת"

word_pat = r'([{alef}-{tav}]+|[0-9./]+|[a-zA-Z]+)'.format(alef=alef, tav=tav)
word_regex = re.compile(word_pat, re.UNICODE | re.MULTILINE)

def remove_all_tags(html):
    html = html.replace('>', '> ')  #to prevent words that are separated by tags only to stick together
    soup = BeautifulSoup(html)
    text = soup.get_text()
    return text

def extract_tokens(s):
    s = remove_all_tags(s)
    ###lst = word_regex.findall(s, re.UNICODE | re.MULTILINE)
    return re.split(r'\s+', s)

def get_reisha(html, size=100):
    punctuation_marks = ',.;?!'
    lst = extract_tokens(html)
    result = ''
    for t in lst:
        if t not in punctuation_marks:
            result += ' '
        result += t
    return result

def guess_language(html):
    s = remove_all_tags(html)
    lang = guess(s)
    pattern = r'[א-ת]+'
    if lang != 'he' and lang != 'en':
        if isinstance(s, unicode):
            s = s.encode('utf8')
        m = re.search(pattern, s)
        if m:
            lang = 'he'
    if language_name(lang).endswith('?'):
        lang = 'UNKNOWN'
    return lang

def tally_words(html, dic, max_freqs, story_id):
    s = remove_all_tags(html)
    lst = extract_words(s)
    if not lst:
        return False
    dic1 = dict()
    for w in lst:
        if w not in dic:
            dic[w] = {}
        if story_id not in dic[w]:
            dic[w][story_id] = 0
        dic[w][story_id] += 1
        if w not in dic1:
            dic1[w] = 0
        dic1[w] += 1
    max_freq = 0
    for w in dic1:
        max_freq = max(max_freq, dic1[w])
    max_freqs[story_id] = max_freq
    return True

def _tally_all_stories():   
    from injections import inject
    db = inject('db')
    dic = dict()
    max_freqs = dict()
    N = 0
    for rec in db(db.TblStories).select():
        html = rec.story
        if tally_words(html, dic, max_freqs, rec.id):
            N += 1
    # calculate average tfidf for each of the words to have them ranked accordingly
    # tf = 0.5 + 0.5 * freq(t, d) / max freq
    # idf = log(1 + N / Nt)
    #avg = 0.0
    #for wrd in dic:
        #for doc_id in dic[wrd]:
            #tf = 0.5 + 0.5 * dic[wrd][doc_id] / max_freqs[doc_id]
            #idf = log(1 + N / len(dic[wrd]))
            #avg = max(avg, tf * idf)
        ####avg = avg / len(dic[wrd])
        #dic[wrd]['*'] = avg

    #test = [(dic[w]['*'], w) for w in dic]
    #test1 = sorted(test, reverse=True)
    #for t in test1[0:100]:
        #print t[1] + ':' + str(t[0])
    return dic

def tally_all_stories(refresh=False):
    c = Cache('tally_all_stories')
    return c(_tally_all_stories, refresh)

def _calc_words_index():
    chunk_size = 100
    dic = _tally_all_stories()
    word_list = sorted(dic.keys())

    sections = []
    for i in range(0, len(word_list), chunk_size):
        lst = word_list[i:i+chunk_size]
        section_dic = dict()
        for wrd in lst:
            section_dic[wrd] = dic[wrd]
        ###word_list_section = [(wrd, dic[wrd]) for wrd in lst]
        key = 'word_index_section-{:03}'.format(i) #first word in the section
        c = Cache(key)
        c(lambda: section_dic, refresh=True)
        sections.append(key)
    return sections

def calc_words_index(refresh=False):
    c = Cache('words_index')
    return c(_calc_words_index, refresh)

def fetch_words_index():
    result = dict()
    sections = calc_words_index()
    for key in sections:
        c = Cache(key)
        dic = c(lambda: dict(nothing='nothing'))  #the code is called only if caching failed
        result.update(dic)
    return result

def _calc_used_languages(used_for):
    db = inject('db')
    dic = {}
    q = (db.TblStories.id > 0)
    if used_for:
        q &= (db.TblStories.used_for==used_for)
    for rec in db(q).select():
        lang = rec.language
        if lang not in dic:
            dic[lang] = 0
        dic[lang] += 1
    lst = []
    for lang in sorted(dic):
        item = dict(id=lang, name='stories.' + language_name(lang), count=dic[lang])
        lst.append(item)
    return dict(used_languages=lst)

def calc_used_languages(vars, refresh=False):
    used_for = int(vars.used_for) if vars.used_for else 2 #STORY4EVENT
    c = Cache('used_languages' + str(used_for))
    return c(lambda: _calc_used_languages(used_for), refresh)

def _get_all_story_previews():
    db = inject('db')
    result = []
    for rec in db(db.TblStories).select(orderby=~db.TblStories.story_len):
        html = rec.story
        preview = get_reisha(html, 30)
        result.append(dict(name=rec.name, id=rec.id, prview=preview))
    return result

def get_all_story_previews(refresh=False):
    c = Cache('get_all_story_previews')
    return c(_get_all_story_previews, refresh)

def test():
    html = 'חיים אבני כותב תוכנית מחשב computer program'
    tally_words

if __name__ == '__main__'    :
    test()




