# coding: utf8

from pycountry import languages
import re

def language_info(lang_code):
    if lang_code.endswith('-'):
        lang_code = lang_code[:-1]
    if len(lang_code) == 2:
        try:
            return languages.get(iso639_1_code=lang_code)
        except:
            return None
    try:
        return languages.get(iso639_3_code=lang_code)
    except:
        try:
            return languages.get(iso639_2T_code=lang_code)
        except:
            return None
        
def language_name(lang_code):
    if not lang_code:
        lang_code = "UNKNOWN"
    if lang_code == "UNKNOWN":
        return lang_code
    code_to_name = dict(
        ar='arabic',
        de='german',
        el='greek',
        en='english',
        es='spanish',
        hu='hungarian',
        it='italian',
        he='hebrew',
        nl='dutch',
        rm='romanian',
        ru='russian'
    )
    return code_to_name.get(lang_code, lang_code + '?')

#Sources for the coding table below: http://unicode-table.com/ and also http://www.utf8-chartable.de/unicode-utf8-table.pl
charsets = [ #ranges of letters unicode used to extract all words from text written in multiple languages
             (
                 (0x0041, 0x005a), (0x0061, 0x007a),                             #basic latin
                 (0x00c0, 0x00d5), (0x00d8, 0x00f6), (0x00f8, 0x01ba),           #extended latin
                 (0x01c4, 0x02af)
                 ),
             (
                 (0x0386, 0x0386), (0x0388, 0x038a), (0x038c, 0x038c),           #Greek and Coptic
                 (0x038e, 0x03a1), (0x03a3, 0x03fb), (0x1f80, 0x1fbc), 
                 (0x1fc2, 0x1fdb), (0x1fe0, 0x1fec), (0x1ff2, 0x1ffc)
                 ),
             (
                 (0x0400, 0x0481), (0x048a, 0x0527), (0xa640, 0xa66e),           #Cyrillic
                 (0xa680, 0xa697)
                 ),
             (
                 (0x0531, 0x0556), (0x0561, 0x0587)                              #Armenian
                 ),
             (
                 (0x05d0, 0x5ea),                                                #Hebrew
                 ),
             (
                 (0x061d, 0x061d), (0x0620, 0x063f), (0x0641, 0x064a),           #Arabic
                 (0x066e, 0x06d3), (0x0750, 0x077f), (0x08a0, 0x08a0), 
                 (0x08a2, 0x08ac), (0xfb50, 0xfbb1), (0xfbd3, 0xfbe9), 
                 (0xfbfc, 0xfbff), (0xfe80, 0xfef4)
                 ),
             (
                 (0x0710, 0x072f), (0x074d, 0x0f4f),                             #Syriac
                 ),
             (
                 (0x0985, 0x098c), (0x098f, 0x0990), (0x0993, 0x09a8),           #Bengali
                 (0x09aa, 0x09b0), (0x09b2, 0x09b2), (0x09b6, 0x09b9), 
                 (0x09ce, 0x09ce), (0x09dc, 0x09dd), (0x09df, 0x09e1)
                 ),
             (
                 (0x0d05, 0x0d0c), (0x0d0e, 0x0d10), (0x0d12, 0x0d3a),           #Malaylam
                 (0x0d4e, 0x0d4e), (0x0d7a, 0x0d7f)
                 ),
             (
                 (0x0e01, 0x0e3a), (0x0e40, 0x0e4f), (0x0e5a, 0x0e5b)            #Thai
                 ),
             (
                 (0x10a0,  0x10c5), (0x10c7, 0x10c7), (0x10cd, 0x10cd),          #Georgian
                 (0x10d0, 0x10fa), (0x10fd, 0x10ff), (0x2d00, 0x2d2d)
             )

]

def blacklist():
    #regex finds characters that should not be included. we must explicitly remove them (or may be learn more about regex and unicode?)
    tuples = []
    for cs in charsets:
        for tup in cs:
            if tup[0] <= 0x201c <= tup[1]:
                pass
            tuples.append(tup)
    tuples = sorted(tuples)
    result = []
    first = 0
    for tup in tuples:
        last = tup[0] - 1
        result.append((first, last))
        first = tup[1] + 1
    return result

def range_pat(tup):
    s = unichr(tup[0])
    if (len(tup) > 1) and (tup[0] != tup[1]):
        s += '-' + unichr(tup[1])
    return s

def lang_pat(seq)        :
    s = u'['
    for tup in seq:
        s += range_pat(tup)
    s += '"\']+'
    return s

def get_emoticons():
    #emoticons taken from http://en.wikipedia.org/wiki/List_of_emoticons
    emoticons = u':-\) :\) :o\) :\] :3 :c\) :> \=\] 8\) \=\) :\} :\^\) :ã£\) '                 # smile, happy
    emoticons += u':-D :D 8-D 8D x-D xD X-D XD =-D =D =-3 =3 B\^D ' + u':-\)\) '   # laugh
    emoticons += u">:\[ :-\( :\( :-c :c :-< :ã£C :< :-\[ :\[ :\{ " + u";\( "          # sad
    emoticons += u':-\|\| :@ >:\( '                                                # angry
    emoticons += u":'-\( :'\( "                                                   # crying
    emoticons += u":'-\) :'\) "                                                   # tears of happiness
    emoticons += u"D:< D: D8 D; D= DX v\.v D-': "                                # great dismay
    emoticons += u">:O :-O :O :-o :o 8-0 O_O o-o O_o o_O o_o O-O "              # surprise, shock, yawn
    emoticons += u":\* :\^\* \('\}\{'\) "                                            # kiss
    emoticons += u">:P :-P :P X-P x-p xp XP :-p :p =p :-Ãž :Ãž :Ã¾ :-Ã¾ :-b :b d: " # Tongue sticking out, cheeky/playful
    emoticons += u">:\ >:/ :-/ :-\. :\ =/ =\ :L =L :S >\.< "                   # Skeptical, annoyed, undecided, uneasy, hesitant
    emoticons += u":\|\|:-\|\| "                                                  # Straight face[4] no expression, indecision
    emoticons += u":\$ "                                                         # Embarrassed 
    emoticons += u":-X :X :-# :# "
    emoticons += u"O:-\) 0:-3 0:3 0:-\) 0:\) 0;\^\) "
    emoticons += u">:\) >;\) >:-\) "
    emoticons += u"o/\\o \^5 >_>\^ \^<_< "                                          # high five
    emoticons += u"\|;-\) \|-O "     

    emoticons += u":-& :& "
    emoticons += u"#-\) "
    emoticons += u"%-\) %\) "
    emoticons += u":-###\.\. :###\.\. "
    emoticons += u"<:-\| "
    emoticons += u"à² _à²  "
    emoticons += u"<\*\)\)\)-\{ ><\(\(\(\*> ><>"

    emoticons = emoticons.strip().replace(' ', '|')
    return emoticons

def multi_language_word_extractor():
    s = u''
    for lang in charsets:
        pat = lang_pat(lang)
        s +=  pat + '|'
    ###s += get_emoticons()
    s = u"[a-z]+(?:[\'â€™]t|[\'â€™]s)|" +  s
    ###s += '| (?P<URL>http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F])))+'
    s = s.encode('utf8')
    return re.compile(s, re.UNICODE | re.IGNORECASE)

_pat = multi_language_word_extractor()
_bl = blacklist()
_emoticons = re.compile(get_emoticons().encode('utf8'))

def remove_annoying_characters(text):
    chars = {
        '\xc2\x82' : ',',        # High code comma
        '\xc2\x84' : ',,',       # High code double comma
        '\xc2\x85' : '...',      # Tripple dot
        '\xc2\x88' : '^',        # High carat
        '\xc2\x91' : '\x27',     # Forward single quote
        '\xc2\x92' : '\x27',     # Reverse single quote
        '\xc2\x93' : '\x22',     # Forward double quote
        '\xc2\x94' : '\x22',     # Reverse double quote
        '\xc2\x95' : ' ',
        '\xc2\x96' : '-',        # High hyphen
        '\xc2\x97' : '--',       # Double hyphen
        '\xc2\x99' : ' ',
        '\xc2\xa0' : ' ',
        '\xc2\xa6' : '|',        # Split vertical bar
        '\xc2\xab' : '<<',       # Double less than
        '\xc2\xbb' : '>>',       # Double greater than
        '\xc2\xbc' : '1/4',      # one quarter
        '\xc2\xbd' : '1/2',      # one half
        '\xc2\xbe' : '3/4',      # three quarters
        '\xca\xbf' : '\x27',     # c-single quote
        '\xcc\xa8' : '',         # modifier - under curve
        '\xcc\xb1' : '',         # modifier - under line
        '\xe2\x80\x9c': '"',
        '\xe2\x80\x9d': '"',
    }

    def replace_chars(match):
        char = match.group(0)
        return chars[char]

    return re.sub('(' + '|'.join(chars.keys()) + ')', replace_chars, text)

utf8_pattern = '''
(?P<good> ([\000-\177]            # 1-byte pattern
     |[\300-\337][\200-\277]      # 2-byte pattern
     |[\340-\357][\200-\277]{2}   # 3-byte pattern
     |[\360-\367][\200-\277]{3}   # 4-byte pattern
     |[\370-\373][\200-\277]{4}   # 5-byte pattern
     |[\374-\375][\200-\277]{5}   # 6-byte pattern
    )+)
| (?P<bad>.)
'''
utf8_regex = re.compile(utf8_pattern, re.MULTILINE | re.DOTALL | re.VERBOSE | re.IGNORECASE)

url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
url_regex = re.compile(url_pattern, re.MULTILINE | re.DOTALL | re.VERBOSE | re.IGNORECASE)

def fix_utf8(text):
    result = ''
    match = utf8_regex.match(text, 0)
    while match:
        start = match.start()
        position = match.end()
        tag = match.lastgroup
        if tag == 'good':
            data = match.group(0)
        else:
            data = '?'
        result += data
        match = utf8_regex.match(text, position)
    return result

def clean_word(w):
    try:
        uin = w.decode('utf8')
    except:
        return w
    uout = u''
    for c in uin:
        if c in '"\':':
            uout += c
            continue
        k = ord(c)
        c1 = c
        for tup in _bl:
            if tup[0] <= k <= tup[1]:
                c1 = ' '
                break
        uout += c1
    #leave only qoutes that are in the middle of a word, for abbrevs
    for c in ('"', "'"):
        if uout.endswith(c):
            uout = uout[:-1]
        if uout.startswith(c):
            uout = uout[1:]
    return uout.encode('utf8') 

def extract_words(s):
    #s = fix_utf8(s)
    #s = remove_annoying_characters(s)
    #s = url_regex.sub('', s)
    if isinstance(s, unicode):
        s = s.encode('utf8')
    result0 = _pat.findall(s)
    result = []
    for w in result0:
        if re.match(r"[a-z]+(?:\'t|\'s)", w, re.UNICODE):
            result.append(w)
        #elif _emoticons.match(w):
            #result.append(w)
        else:
            w = clean_word(w).strip()
            if w:
                if '"' in w:
                    b = w.startswith('"')
                if "'" in w:
                    b = w.startswith("'")
                for w1 in re.split(r'\s+', w):
                    #if non_word_regex.match(w1):
                        #continue
                    result.append(w1)
    return result

def test():
    s = '×—×™×™× ××‘× ×™ 1234  raanana' 
    s += r" I don't know what it's meaning is :-) ------ >;)  )))=====  ('}{') "
    s += r'â€œWe at http://www.coolano.com/1234?boom=5678&koom=123xCs_y-Yy donâ€™t report export volumes ' + chr(0x93)
    s += "חיים אבני תב תוכנית יפה "
    s += 'לא הייתי בפלמ"ח, אני לא "גבר"?'
    s += 'pal"mach'
    lst = extract_words(s)
    for i, x in enumerate(lst):
        print '{:3} word:  {} '.format(i, x)
            
if __name__ == '__main__':
    test()