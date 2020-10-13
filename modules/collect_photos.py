import os
import datetime

#just for experiments. may be deleted soon

def modification_date(filename):
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)

def add_photos_from_drive(root_folder):
    for root, dirs, files in os.walk(root_folder, topdown=True):
        print(("there are", len(files), "files in", root))
        for f in files[:4]:
            d = modification_date(root + '/' + f)

def main():
    add_photos_from_drive('/gb_photos/gbs/photos/orig/uploads')
    
if __name__ == '__main__'    :
    main()
