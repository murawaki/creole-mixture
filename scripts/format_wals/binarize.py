# -*- coding: utf-8 -*-
#
import sys, os
import codecs
import json

sys.path.insert(1, os.path.join(sys.path[0], os.path.pardir))
from json_utils import load_json_file, load_json_stream


def main(src, fpath, dst, fpath2):
    fid2struct = load_json_file(fpath)

    with codecs.getwriter("utf-8")(open(dst, 'w')) as f:
        for i, lang in enumerate(load_json_stream(open(src))):
            rv = ""
            for struct in fid2struct:
                flen = len(struct["vid2label"])
                _arr = ["0"] * flen
                wals_id = struct["wals_id"]
                v = lang["features_filled"][wals_id]
                _arr[v] = "1"
                rv += "".join(_arr)
            lang["bin"] = rv
            f.write("%s\n" % json.dumps(lang))

    flist_bin = []
    for struct in fid2struct:
        name = struct["name"]
        for v in struct["vid2label"]:
            flist_bin.append("%s\t%s" % (name, v))
    with codecs.getwriter("utf-8")(open(fpath2, 'w')) as f:
        f.write("%s\n" % json.dumps(flist_bin))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
