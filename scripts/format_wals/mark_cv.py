# -*- coding: utf-8 -*-
#
import sys, os
import codecs
import json
import random
from argparse import ArgumentParser

sys.path.insert(1, os.path.join(sys.path[0], os.path.pardir))
from json_utils import load_json_file, load_json_stream


def main():
    parser = ArgumentParser()
    parser.add_argument("-s", "--seed", dest="seed", metavar="INT", type=int, default=None,
                        help="random seed")
    parser.add_argument("--cv", dest="cv", metavar="INT", type=int, default=5,
                        help="N-fold cross-validation")
    parser.add_argument("_in", metavar="INPUT", help="input")
    parser.add_argument("_out", metavar="OUTPUT", help="output")
    args = parser.parse_args()

    sys.stderr.write("%d-fold cross validation\n" % args.cv)

    if args.seed is not None:
        random.seed(args.seed)

    langs = []
    cvns = []
    for i, lang in enumerate(load_json_stream(open(args._in))):
        langs.append(lang)
        cvns.append(i % args.cv)
    random.shuffle(cvns)

    with codecs.getwriter("utf-8")(open(args._out, 'w')) as f:
        for lang, cvn in zip(langs, cvns):
            lang["cvn"] = cvn
            f.write("%s\n" % json.dumps(lang))

if __name__ == "__main__":
    main()
