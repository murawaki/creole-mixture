# -*- coding: utf-8 -*-

import sys
import json
import codecs
from bz2 import BZ2File

def load_json_file(fname):
    if fname.endswith(".bz2"):
        reader = codecs.getreader("utf-8")(BZ2File(fname))
    else:
        reader = codecs.getreader("utf-8")(open(fname))
    dat = reader.read()
    return json.loads(dat)

def load_json_stream(f, offset=0):
    # do not apply codecs to f; this is too slow!
    for i, line in enumerate(f):
        if i >= offset:
            line = codecs.decode(line, "utf8")
            yield json.loads(line)
        else:
            if i % 1 == 10:
                sys.stderr.write("#\n")
