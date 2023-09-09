src_name = "/home/haim/server_src/models/db_gbs.py"
dst_name = "/home/haim/fixes/db_gbs_new.py"
dic = dict()
table_name = ""
with open(src_name) as f:
    with open(dst_name, "w") as g:
        for s in f:
            if "define_table" in s:
                r1 = s.find("(")
                r2 = s.rfind(",")
                table_name = s[r1+2:r2-1]
                if table_name not in dic:
                    dic[table_name] = []

            if "Field('" in s:
                r1 = s.find("Field('") +7
                r2 = s.find("',")
                column_name = s[r1:r2]
                if column_name != column_name.lower():
                    dic[table_name].append(column_name)
                    s = s.replace(column_name, column_name.lower())
            g.write(s)

with open("/home/haim/fixes/lowercase.sql", "w") as f:
    for k in dic:
        if len(dic[k]) == 0:
            continue
        print(f"table [{k}]")
        for col in dic[k]:
            print(f"    column: {col}")
            cmd = f'ALTER TABLE "{k}" RENAME "{col}" to {col.lower()};\n'
            f.write(cmd)
