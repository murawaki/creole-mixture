# -*- coding: utf-8 -*-
import sys, os
import codecs
import copy
import json
from argparse import ArgumentParser
from collections import defaultdict

sys.path.insert(1, os.path.join(sys.path[0], os.path.pardir))
from csv_utils import UnicodeReader
from json_utils import load_json_stream, load_json_file


def main():
    parser = ArgumentParser()
    parser.add_argument("walslangs", metavar="WALS_LANGS", default=None)
    parser.add_argument("walsfeatures", metavar="WALS_FEATURES", default=None)
    parser.add_argument("apicslangs", metavar="APiCS_LANGS", default=None)
    parser.add_argument("merged", metavar="MERGED", default=None)
    parser.add_argument("flist", metavar="FLIST", default=None)
    args = parser.parse_args()

    wals_langs = {}
    for lang in load_json_stream(open(args.walslangs)):
        wals_langs[lang["name"]] = lang
    fid2struct = load_json_file(args.walsfeatures)

    apics_langs = {}
    for lang in load_json_stream(open(args.apicslangs)):
        apics_langs[lang["name"]] = lang

    # count features used in apics
    feature2count = defaultdict(float)
    for name, lang in apics_langs.iteritems():
        for wals_id, v in lang["features"].iteritems():
            feature2count[wals_id] += 1

    # shrink features
    fid2struct2 = []
    for struct in fid2struct:
        if struct["wals_id"] in feature2count:
            struct["idx"] = len(fid2struct2)
            fid2struct2.append(struct)
    fid2struct = fid2struct2

    # shrink features property of each WALS language
    for name in wals_langs.keys():
        lang = wals_langs[name]
        lang["source"] = "WALS"
        lang["orig_features"] = copy.copy(lang["features"])
        for wals_id in lang["features"].keys():
            if wals_id not in feature2count:
                del lang["features"][wals_id]

    with codecs.getwriter("utf-8")(open(args.merged, 'w')) as f:
        for _l in (apics_langs, wals_langs):
            for name, lang in _l.iteritems():
                f.write("%s\n" % json.dumps(lang))

    with codecs.getwriter("utf-8")(open(args.flist, 'w')) as f:
        f.write("%s\n" % json.dumps(fid2struct))

if __name__ == "__main__":
    main()
