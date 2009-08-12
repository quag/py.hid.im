import hashlib
import itertools
import math

import png

_magic = [104, 105, 100, 105, 109, 32, 105, 115, 32, 116, 111, 114, 114, 101, 110, 116, 115, 33]
_magicstring = ''.join(chr(b) for b in _magic)

_logo = ["#   #   #   #      ",
         "#       #          ",
         "##  #  ##   # ## # ",
         "# # # # #   # # # #",
         "# # # ### # # # # #"]

class _PixelMap:
    def __init__(self, width, height, data, pixelsize):
        self._width = width
        self._height = height
        self._data = list(data)
        self._pixelsize = pixelsize

    def __getitem__(self, (x, y, c)):
        return self._data[y][x * self._pixelsize + c]

    def __setitem__(self, (x, y, c), value):
        self._data[y][x * self._pixelsize + c] = value

    def setPixel(self, (x, y), (r, g, b)):
        self[x, y, 0] = r
        self[x, y, 1] = g
        self[x, y, 2] = b

    def first(self):
        return (0, self._height - 1, 0)

    def next(self, (x, y, c), ystart=None, linelength=None):
        if ystart == None:
            ystart = self._height - 1

        if linelength == None:
            linelength = ystart + 1

        c += 1

        if c == 3:
            c = 0
            y -= 1

            if y == ystart - linelength:
                y = ystart
                x += 1

        return (x, y, c)

class _Reader:
    def __init__(self, img, location):
        self._img = img
        self.location = location

        self.left = location[0]
        self.ystart = location[1]
        self.linelength = self.ystart + 1

    def skip(self, n=1):
        for i in range(n):
            self.location = self._img.next(self.location, self.ystart, self.linelength)

    def read(self, n=None):
        if n == None:
            b = self._img[self.location]
            self.skip()
            return chr(b)
        else:
            bytes = []

            for i in range(n):
                bytes.append(self.read())

            return ''.join(bytes)

    def readBenInteger(self):
        if self.read() != 'i':
            raise DecodeError()

        number = 0
        while True:
            c = self.read()

            if c == 'e':
                break
            elif c.isdigit():
                number = (number * 10) + int(c)
            else:
                raise DecodeError()

        return number

    def readBenString(self):
        length = 0
        while True:
            c = self.read()

            if c == ':':
                break
            elif c.isdigit():
                length = (length * 10) + int(c)
            else:
                raise DecodeError()

        return self.read(length)

class _Writer:
    def __init__(self, img, left, ystart, linelength):
        self._img = img
        self.location = (left, ystart, 0)

        self.ystart = ystart
        self.linelength = linelength

    def write(self, b):
        self._img[self.location] = b
        self.location = self._img.next(self.location, self.ystart, self.linelength)

class DecodeError(Exception):
    pass

def decode(filename):
    (width, height, data, meta) = png.Reader(filename).read()

    if meta["greyscale"] or meta["bitdepth"] != 8:
        raise DecodeError()

    img = _PixelMap(width, height, data, pixelsize=meta["planes"])

    p = img.first()

    while True:
        if img[p] == _magic[0]:
            start = True
            q = p
            for b in _magic:
                if b != img[q]:
                    start = False
                    break
                else:
                    q = img.next(q)

            if start:
                break

        p = img.next(p)

    if p[2] != 0:
        raise DecodeError()

    reader = _Reader(img, p)
    reader.skip(len(_magic))
    reader.linelength = reader.readBenInteger()
    embeddedFileName = reader.readBenString()
    sha1Hash = reader.readBenString()
    dataLength = reader.readBenInteger()

    data = reader.read(dataLength)

    actualHash = _sha1(data)

    if sha1Hash == actualHash:
        return (embeddedFileName, data)

    return None

def _benInt(x):
    return "i" + str(x) + "e"

def _benStr(s):
    return str(len(s)) + ":" + s

def encode(filename, data, file, targetsize=(600, 30)):
    targetwidth, targetheight = targetsize

    sha1Hash = _sha1(data)

    height = max(len(data) / 3 / targetwidth, targetheight, len(_logo[0]))
    payload = _magicstring + _benInt(height) + _benStr(filename) + _benStr(sha1Hash) + _benInt(len(data)) + data
    width = int(math.ceil(float(len(payload)) / height / 3))

    left = len(_logo) + 1

    imgWidth = left + width + 1
    imgHeight = 1 + height + 1

    rows = []
    for y in range(imgHeight):
        rows.append(list(itertools.repeat(0, imgWidth * 3)))

    img = _PixelMap(imgWidth, imgHeight, rows, 3)
    writer = _Writer(img, left, 1 + (height-1), height)

    for x in range(len(_logo)):
        for y in range(len(_logo[0])):
            if not _logo[x][y].isspace():
                img.setPixel((1 + x, imgHeight - 2 - y), (255, 255, 255))

    for c in payload:
        writer.write(ord(c))

    w = png.Writer(imgWidth, imgHeight)
    w.write(file, rows)

def _sha1(s):
    h = hashlib.sha1()
    h.update(s)
    return h.hexdigest()

