#
# features derived from the restructurer
#
import sys, os
from argparse import ArgumentParser
import codecs
import numpy as np
from scipy.misc import logsumexp
from collections import defaultdict

sys.path.insert(1, os.path.join(sys.path[0], os.path.pardir))
from json_utils import load_json_file, load_json_stream


def fix_order(abc):
    # NOTE: data order: R, L, S  and  plot order L, S, R
    return np.array([abc[1], abc[2], abc[0]])

def main():
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout)
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr)

    parser = ArgumentParser()
    parser.add_argument("--type", metavar="POINT_TYPE", default="theta")
    parser.add_argument("--output", metavar="IMG", default=None)
    parser.add_argument("dumps", metavar="DUMP", default=None)
    parser.add_argument("langs", metavar="LANG", default=None)
    parser.add_argument("flist", metavar="FLIST", default=None)
    args = parser.parse_args()

    burnin = 51

    fid2struct = load_json_file(args.flist)
    langs = {}
    for lang in load_json_stream(open(args.langs)):
        if lang["source"] == "APiCS":
            langs[lang["name"]] = lang

    # stats = np.zeros(len(bin_flist))
    # points = []
    fcount = defaultdict(int)
    samples = 0
    total = 0
    rtotal = 0

    stream = load_json_stream(open(args.dumps))
    for i in xrange(burnin):
        stream.next()
    for dump in stream:
        # lang_num = len(dump['mixlist'])
        for creole in dump['mixlist']:
            catvect = langs[creole["langname"]]["catvect_filled"]
            total += 1
            for j, val in enumerate(creole["assignments"]):
                if val == 0:
                    rtotal += 1
                    vid = catvect[j]
                    flabel = fid2struct[j]["name"] + "\t" + fid2struct[j]["vid2label"][vid]
                    fcount[flabel] += 1
        samples += 1

    total = float(total)
    rtotal = float(rtotal)
    _sorted = sorted(fcount.keys(), key=lambda x: fcount[x], reverse=True)
    cum = 0
    for flabel in _sorted:
        cum += fcount[flabel]
        sys.stdout.write("%d\t%f\t%f\t%s\n" % (fcount[flabel], fcount[flabel] / total, cum / rtotal, flabel))

if __name__ == "__main__":
    main()
