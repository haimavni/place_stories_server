# coding: utf-8

"""
Extract PDF text using PDFMiner. Adapted from
http://stackoverflow.com/questions/5725278/python-help-using-pdfminer-as-a-library
"""

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter#process_pdf
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams

from cStringIO import StringIO
import re

import textract

def pdf_to_text111(pdfname):
    text = textract.process(pdfname, method='pdfminer', language='hebrew')

    return text

def pdf_to_text(pdfname):
    pat = '[א-תךםןףץ]'
    pat = pat.replace('[', '[^ ').replace(']',']{2,100}')
    pat = pat.decode('utf-8')
    r = re.compile(pat, flags=re.U)

    # PDFMiner boilerplate
    rsrcmgr = PDFResourceManager()
    sio = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, sio, codec=codec, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    # Extract text
    fp = file(pdfname, 'rb')
    for page in PDFPage.get_pages(fp):
        interpreter.process_page(page)
    fp.close()

    # Get text from StringIO
    text = sio.getvalue()
    text1 = text.decode('utf-8')
    lst = text1.split('\n')
    text2 = '<html>\n<head>\n<meta charset="utf-8">\n</head>\n<body dir="RTL">\n'
    for s in lst:
        s = reverse(s)
        ###s = s.replace('(', '~~').replace(')', '(').replace('~~', ')')
        s = r.sub(invert, s)
        text2 += s + '<br/>'
    text2 += '\n</body>\n</html>'
    text2 = text2.encode('utf-8')
    ###text2 = r.sub(invert, text1)
    #with open('/home/haim/test1.html', 'w') as f:
        #f.write(text2)

    # Cleanup
    device.close()
    sio.close()

    return text2

def reverse(s):
    result = ''
    for c in s:
        result = c + result
    return result

def invert(m):
    s = m.group(0)
    return reverse(s)

if __name__ == '__main__':

    path = '/home/haim/yoman.pdf'
    text = pdf_to_text(path)

    print text
