#!/usr/bin/env python
import os
import sys

import hidim

for fileName in sys.argv[1:]:
    embeddedFileName, data = hidim.decode(fileName)

    outName = os.path.split(embeddedFileName)[1]
    print outName

    f = open(outName, 'w')
    f.write(data)
    f.close()
