#
# summarize assignment variables (Fact per-feature, Fact per-creole)
#
import sys, os
from argparse import ArgumentParser
import codecs
import numpy as np
from scipy.misc import logsumexp

sys.path.insert(1, os.path.join(sys.path[0], os.path.pardir))
from json_utils import load_json_file, load_json_stream


def fix_order(abc):
    # NOTE: data order: R, L, S  and  plot order L, S, R
    return np.array([abc[1], abc[2], abc[0]])

def main():
    parser = ArgumentParser()
    parser.add_argument("--type", metavar="POINT_TYPE", default="theta")
    parser.add_argument("--output", metavar="IMG", default=None)
    parser.add_argument("dumps", metavar="LANG", default=None)
    args = parser.parse_args()

    fsize=24
    subdiv=8
    burnin = 51

    stats = np.zeros(3)
    points = []
    samples = 0

    stream = load_json_stream(open(args.dumps))
    for i in xrange(burnin):
        stream.next()
    for dump in stream:
        if args.type == "feature":
            for j, mu in enumerate(dump['mus']):
                _sum = logsumexp(mu)
                probs = np.exp(mu - _sum)
                probs2 = fix_order(probs)
                points.append(probs2)
                stats += probs2
        elif args.type == "lang":
            for creole in dump['mixlist']:
                etas = np.array(creole['etas'])
                _sum = logsumexp(etas)
                probs = np.exp(etas - _sum)
                probs2 = fix_order(probs)
                points.append(probs2)
                stats += probs2
        samples += 1

    _sum = float(sum(stats))
    sys.stdout.write("%d samples\n" % samples)
    sys.stdout.write("%f\t%f\t%f\n" % (stats[0] / _sum, stats[1] / _sum, stats[2] / _sum))

if __name__ == "__main__":
    main()
