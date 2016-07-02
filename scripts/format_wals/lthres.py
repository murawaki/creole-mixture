# -*- coding: utf-8 -*-
#
# filter out languages by feature coverage
#
import sys, os
import codecs
import json
from argparse import ArgumentParser

sys.path.insert(1, os.path.join(sys.path[0], os.path.pardir))
from json_utils import load_json_file, load_json_stream


def main():
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr)

    parser = ArgumentParser()
    parser.add_argument("--lthres", dest="lthres", metavar="FLOAT", type=float, default=0.0,
                        help="eliminate languages with higher rate of missing values [0,1]")
    parser.add_argument("langs_all", metavar="INPUT", default=None)
    parser.add_argument("flist", metavar="FLIST", default=None)
    parser.add_argument("langs", metavar="OUTPUT", default=None)
    args = parser.parse_args()

    fid2struct = load_json_file(args.flist)
    fsize = len(fid2struct)
    sys.stderr.write("%d featurs\n" % fsize)

    lang_total, lang_survived = 0, 0
    with codecs.getwriter("utf-8")(open(args.langs, "w")) as out:
        for lang in load_json_stream(open(args.langs_all)):
            lang_total += 1
            if float(len(lang["features"])) / fsize >= args.lthres:
                lang_survived += 1
                out.write("%s\n" % json.dumps(lang))

    sys.stderr.write("language thresholding: %d -> %d\n" % (lang_total, lang_survived))


if __name__ == "__main__":
    main()
