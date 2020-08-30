# -*- coding: utf-8 -*-

import csv
import sys
import glob
from gluon.storage import Storage
from old_db_mappings import fields_template

n = -1
alef = 'א'
alef = alef.decode('utf-8')

def ascii2unicode(s, base=224):
    if isinstance(s, str):
        s = s.decode('utf8')
    u = u''
    for c in s:
        if ord(c) >= base:
            c = unichr(ord(alef) + ord(c) - base)
        u += c
    return u

def fix_field_name(fld):
    #replace names that are reserved or taken
    if fld == 'ID':
        return 'IIDD'
    elif fld == 'Source':
        return 'SSource'
    else:
        return fld
    
def table_fields(csv_name):
    with open(csv_name, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        fields = reader.next()
        fields = [fix_field_name(f) for f in fields]
        return fields

def csv_name_to_table_name(csv_name):
    return csv_name.split()[-1][:-4]
    
def write_field_types(csv_name, out):
    table_name = csv_name_to_table_name(csv_name)
    out.write('    alldefs["{}"] = dict(\n'.format(table_name))
    fields = table_fields(csv_name)
    s = ''
    for field in fields:
        out.write("        {f}='string',\n".format(f=field))
        if len(field) > 2 and field.endswith('ID'):
            if not s:
                s =  '    ' + table_name + '=['
            s += field + ', '
    if s:
        s = s[:-2] + ']'
        print s
        
    out.write("    )\n\n")
    
def write_all_field_types(base_dir='/home/haim/fossil_projects/gbs/private/gbs-bkp-jun16/'):
    out_name = base_dir + 'old_db_mappings.py'
    out = open(out_name, 'w')
    out.write('def fields_template():\n\n')
    out.write('    alldefs = dict()\n\n')
    lst = glob.glob(base_dir + '*.csv')
    lst = sorted(lst)
    for csv_name in lst:
        write_field_types(csv_name, out)
    out.write('    return alldefs')

###write_table_definition(csv_name)

def get_records(csv_name):
    mapa = fields_template()
    table_name = csv_name_to_table_name(csv_name)
    field_map = mapa[table_name]
    with open(csv_name, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        reader.next()     #skip header
        field_names = table_fields(csv_name)
        for row in reader:
            result = Storage()
            for i, v in enumerate(row):
                fname = field_names[i]
                typ = field_map[fname]
                if typ in ['string', 'text']:
                    u = ascii2unicode(v)
                elif typ == 'integer':
                    u = int(v) if v else None
                elif typ == 'boolean':
                    u = True if v == 'TRUE' else False
                else:
                    raise Exception('unknown field type')
                result[fname] = u
            yield result
        
def insert_data(csv_name):
    with open(csv_name, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
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
                
if __name__ == '__main__':
    write_all_field_types()
