# -*- coding: utf-8 -*-

import csv
import sys

csv_name = 'TblPhotos.csv'
csv_name = 'haim-97 - ' + csv_name
n = -1
alef = 'א'
alef = alef.decode('utf-8')

def ascii2unicode(s, base=224):
    u = ''
    for c in s:
        if ord(c) >= base:
            c = chr(ord(alef) + ord(c) - base)
        u += c
    return u

def table_fields(csv_name):
    with open(csv_name, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        return next(reader)

def write_table_definition(csv_name, out=sys.stdout):
    table_name = csv_name[10:-4]
    out.write("db.define_table('{t}',\n".format(t=table_name))
    fields = table_fields(csv_name)
    for field in fields:
        out.write("                Field('{f}'),\n".format(f=field))
    out.write("                )\n\n")

write_table_definition(csv_name)

def get_records(csv_name):
    with open(csv_name, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    field_names = next(reader)    
    for row in reader:
        result = dict()
        for i, v in enumerate(row):
            u = ascii2unicode(v)
            result[field_names[i]] = u
        yield result
        
with open(csv_name, 'rb') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in spamreader:
        n += 1
        if n > 150:
            break
        if n == 0:
            header = row
        else:
            print(n)
            for i, v in enumerate(row):
                u = ascii2unicode(v) 
                print('    ' + header[i], ' = ', u)
                j = 999

