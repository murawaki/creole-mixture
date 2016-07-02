# -*- coding: utf-8 -*-
import sys, os
import codecs
import json

sys.path.insert(1, os.path.join(sys.path[0], os.path.pardir))
from json_utils import load_json_file, load_json_stream

def main(orig, src, fpath, dst):
    fid2struct = load_json_file(fpath)

    with open(src) as fin:
        fin.readline() # ignore the header
        with codecs.getwriter("utf-8")(open(dst, 'w')) as fout:
            for lang, l in zip(load_json_stream(open(orig)), fin):
                lang["features_filled"] = {}
                l = l.rstrip()
                a = l.split("\t")
                label = a.pop(0)
                for fid, v in enumerate(a):
                    wals_id = fid2struct[fid]["wals_id"]
                    lang["features_filled"][wals_id] = int(v)
                    assert(wals_id not in lang["features"] or lang["features"][wals_id] == int(v))
                fout.write("%s\n" % json.dumps(lang))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
