# -*- coding: utf-8 -*-
#
# convert WALS ID-based features into categorical vectors
#
import sys, os
import codecs
import json
from argparse import ArgumentParser
from collections import defaultdict

sys.path.insert(1, os.path.join(sys.path[0], os.path.pardir))
from json_utils import load_json_file, load_json_stream

def create_cat_vect(fid2struct, features):
    catvect = [-1 for i in xrange(len(fid2struct))]
    for i, struct in enumerate(fid2struct):
        wals_id = struct["wals_id"]
        if wals_id in features:
            # not "fid" is the original WALS id; "idx" is affected by shrinkage
            assert(i == struct["idx"])
            catvect[struct["idx"]] = features[wals_id]
    return catvect

def main():
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr)

    parser = ArgumentParser()
    parser.add_argument("langs_in", metavar="LANGS_IN", default=None)
    parser.add_argument("flist_in", metavar="FLIST_IN", default=None)
    parser.add_argument("langs_out", metavar="LANGS_OUT", default=None)
    args = parser.parse_args()

    fid2struct = load_json_file(args.flist_in)
    with codecs.getwriter("utf-8")(open(args.langs_out, 'w')) as f:
        for lang in load_json_stream(open(args.langs_in)):
            lang["catvect"] = create_cat_vect(fid2struct, lang["features"])
            if "features_filled" in lang:
                lang["catvect_filled"] = create_cat_vect(fid2struct, lang["features_filled"])
            f.write("%s\n" % json.dumps(lang))

if __name__ == "__main__":
    main()
