# -*- coding: utf-8 -*-

import csv
import sys
import glob

n = -1
alef = 'א'
alef = alef.decode('utf-8')

def ascii2unicode(s, base=224):
    u = u''
    for c in s:
        if ord(c) >= base:
            c = unichr(ord(alef) + ord(c) - base)
        u += c
    return u

def table_fields(csv_name):
    with open(csv_name, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        return reader.next()

def csv_name_to_table_name(csv_name):
    return csv_name.split()[-1][:-4]
    
def write_field_types(csv_name, out):
    table_name = csv_name_to_table_name(csv_name)
    out.write('    alldefs["{}"] = dict(\n'.format(table_name))
    fields = table_fields(csv_name)
    for field in fields:
        out.write("        {f}='string',\n".format(f=field))
    out.write("    )\n\n")
    
def write_all_field_types(base_dir='/home/haim/fossil_projects/gbs/private/old_db/'):
    out_name = base_dir + 'old_db_mappings.py'
    out = open(out_name, 'w')
    out.write('def fields_template():\n\n')
    out.write('    alldefs = dict()\n\n')
    for csv_name in glob.glob(base_dir + '*.csv'):
        write_field_types(csv_name, out)
    out.write('    return alldefs')

###write_table_definition(csv_name)

def get_records(csv_name):
    with open(csv_name, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    field_names = reader.next()    
    for row in reader:
        result = dict()
        for i, v in enumerate(row):
            u = ascii2unicode(v)
            result[field_names[i]] = u
        yield result
        
def insert_data(csv_name):
    with open(csv_name, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in spamreader:
            n += 1
            if n > 150:
                break
            if n == 0:
                header = row
            else:
                print n
                for i, v in enumerate(row):
                    u = ascii2unicode(v) 
                    print '    ' + header[i], ' = ', u
                    j = 999
                
write_all_field_types()
