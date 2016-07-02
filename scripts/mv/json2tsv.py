# -*- coding: utf-8 -*-
#
# output TSV file for imput_mca.r
#
import sys, os
import codecs
import json

sys.path.insert(1, os.path.join(sys.path[0], os.path.pardir))
from json_utils import load_json_file, load_json_stream


def main(src, fpath, dst):
    fid2struct = load_json_file(fpath)

    with codecs.getwriter("utf-8")(open(dst, 'w')) as f:
        rv = "\t".join([struct["name"] for struct in fid2struct])
        f.write(rv + "\n")

        for i, lang in enumerate(load_json_stream(open(src))):
            rv = str(i) + "\t"
            for struct in fid2struct:
                wals_id = struct["wals_id"]
                if wals_id in lang["features"]:
                    v = lang["features"][wals_id]
                    rv += str(int(v)) + "\t"
                else:
                    rv += "NA\t"
            rv = rv[0:len(rv) - 1]
            f.write(rv + "\n")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
