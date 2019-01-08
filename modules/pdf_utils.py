# coding: utf-8

'''
pdf utils:
    convert pdf to html
    higlight words in pdf
'''
import re
import fitz

PAT = '[א-תךםןףץ]'
PAT_HEB = PAT.replace(']', ']{2,100}').decode('utf-8')
HEB_REGEX = re.compile(PAT_HEB, flags=re.U)
PAT_LAAZ = PAT.replace('[', '[^ ').replace(']', ']{2,100}').decode('utf-8')
LAAZ_REGEX = re.compile(PAT_LAAZ, flags=re.U)

def detect_rtl(doc):
    '''
    some docs have their whole lines reversed and some have their words reversed.
    use position of commas to decide. ugly...
    '''
    pat1 = PAT_HEB + ','
    pat2 = ',' + PAT_HEB
    regex1 = re.compile(pat1, flags=re.U)
    regex2 = re.compile(pat2, flags=re.U)
    n1 = 0
    n2 = 0
    for page in doc:
        text = page.getText()
        lst = text.split('\n')
        #make sure we are not biased by missing space between comma and the following word
        for tmp_s in lst:
            if regex1.search(tmp_s): 
                n1 += 1
            if regex2.search(tmp_s):
                n2 += 1
            if n1 - n2 > 10:
                return False
            elif n2 - n1 > 10:
                return True
    return n2 > n1

def pdf_to_text(pdfname):
    '''pdf to html'''
    doc = fitz.open(pdfname)
    rtl_lines = detect_rtl(doc)
    result = '<html>\n<head>\n<meta charset="utf-8">\n</head>\n<body dir="RTL">\n'
    for page in doc:
        text = page.getText()
        lst = text.split('\n')
        for tmp_s in lst:
            if rtl_lines:
                if HEB_REGEX.search(tmp_s):
                    tmp_s = reverse(tmp_s)
                    tmp_s = LAAZ_REGEX.sub(invert, tmp_s) #reverse non-hebrew words back
            else:
                tmp_s = HEB_REGEX.sub(invert, tmp_s)
            result += tmp_s + '\n'
    result += '\n</body>\n</html>'
    result = result.encode('utf-8')
    return result

def highlight_pdf(fname, outfname, keywords):
    '''
    highlight keywords in pdf files
    '''
    doc = fitz.open(fname)
    if not isinstance(keywords, list):
        keywords = [keywords]
    keywords = [w if isinstance(w, unicode) else w.decode('utf-8') for w in keywords]
    for kwd in keywords:
        if HEB_REGEX.match(kwd):
            kwd = reverse(kwd)
        for page in doc:
            text_instances = page.searchFor(kwd)
            for inst in text_instances:
                page.addHighlightAnnot(inst)
    doc.save(outfname, garbage=4, deflate=True, clean=True)

def test_highlight():
    '''
    test
    '''
    fname = "/home/haim/pdf_tests/yoman.pdf"
    outfname = "/home/haim/yoman_highlighted.pdf"
    kw1 = "המונדיאל"
    kw2 = "המוסיקה"
    kw3 = "הנסיעה"
    kw4 = "המשפחות"
    highlight_pdf(fname, outfname, [kw1, kw2, kw3, kw4])

def test_pdf2text():
    import sys
    fname = sys.argv[1] if len(sys.argv) > 1 else 'yoman'
    '''test pdf to text'''
    pdfname = '/home/haim/pdf_tests/{}.pdf'.format(fname)
    html = pdf_to_text(pdfname)
    htmlname = pdfname.replace('.pdf', '.html')
    with open(htmlname, 'w') as tmp_f:
        tmp_f.write(html)

def reverse(tmp_s):
    '''reverse string'''
    result = ''
    for tmp_c in tmp_s:
        result = tmp_c + result
    return result

def invert(match):
    '''callback'''
    tmp_s = match.group(0)
    return reverse(tmp_s)

if __name__ == '__main__':
    test_pdf2text()
    test_highlight()
    print 'done'
    