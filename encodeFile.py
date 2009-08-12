#!/usr/bin/env python
import os
import sys

import hidim

def readFile(fileName):
    chunks = []
    f = open(fileName, 'rb')

    while True:
        chunk = f.read()
        
        if len(chunk) == 0:
            break

        chunks.append(chunk)

    return ''.join(chunks)


for path in sys.argv[1:]:
    data = readFile(path)

    name = os.path.split(path)[1]
    outName = os.path.splitext(name)[0] + ".png"

    f = open(outName, 'wb')
    hidim.encode(name, data, f)
    f.close()

    print outName
