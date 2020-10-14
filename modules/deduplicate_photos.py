import dhash
from pybktree import BKTree, hamming_distance
##from injections import inject
from PIL import Image

SIZE = 8

def hash_photo(photo_path):
    img = Image.open(photo_path)
    return dhash.dhash_int(img, SIZE)

def test():
    photo_path = '/gb_photos/gbs/photos/uploads/2018-01/'
    photos = ['10ab78e.jpg',  '3a861357.jpg', '67c677b1.jpg', 'a541fef8.jpg', 'df7290ee.jpg',
              '19a65c98.jpg', '4b8916af.jpg', '6a056f3b.jpg', 'ac0fdd94.jpg', 'e0089400.jpg',
              '22331c8b.jpg', '4da078e4.jpg', '78d4488.jpg',  'bc2d361d.jpg', 'e4d8b370.jpg',
              '2543ac35.jpg', '4dd1e373.jpg', '7aa820d3.jpg', 'be52aec0.jpg', 'f1f86d90.jpg',
              '29f614f2.jpg', '4fb0c35c.jpg', '8167f4a6.jpg', 'c2b4569d.jpg', 'ff78c098.jpg',
              '2cc6d25d.jpg', '604868e6.jpg', '83ea5c22.jpg', 'cbcacc20.jpg', 'ffaef93f.jpg',
              '30cfbac5.jpg', '6062f3c1.jpg', '8c073faa.jpg', 'ccc2fb52.jpg',
              '375a2516.jpg', '64823f43.jpg', '9d51e8ff.jpg', 'd13fb248.jpg']
    tree = BKTree(hamming_distance)
    n = 0
    for fname in photos:
        path = photo_path + fname
        hv = hash_photo(path)
        print(('{:3}  {:X}'.format(n, hv)))
        n += 1
        tree.add(hv)
        
    print(tree)

if __name__ == '__main__':
    test()



