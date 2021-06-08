from array import array
import binascii

table = array('L')


def create_table():
    poly = 0xEDB88320

    for byte in range(256):
        crc = 0
        for bit in range(8):
            if (byte ^ crc) & 1:
                crc = (crc >> 1) ^ poly
            else:
                crc >>= 1
            byte >>= 1
        table.append(crc)


create_table()


def crc32(buff, value=None):
    value = value if value else 0xffffffff
    i = 0
    for x in buff:
        value = table[(x ^ value) & 0xff] ^ (value >> 8)
        i += 1

    return -1 - value


def test():
    data = (
        '',
        'test',
        'hello world',
        '1234',
        'A long string to test CRC32 functions',
    )

    for s1 in data:
        s = bytearray(s1, 'utf-8')
        print(repr(s))
        a = binascii.crc32(s)
        print('%08x' % (a & 0xffffffff))
        b = crc32(s)
        print('%08x' % (b & 0xffffffff))

    arr = [x for x in range(100)]
    buff = bytearray(arr)
    a = binascii.crc32(buff)
    b = crc32(buff)
    c = -1 - b ^ 0xffffffff
    print(f" a={a:x} b={b:x} -b={-b:x}  bf={c:x}")


if __name__ == '__main__':
    test()