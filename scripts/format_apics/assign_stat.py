#
# summarize assignment variables (Mono, Fact-combined)
#
import sys, os
from argparse import ArgumentParser
import codecs
import numpy as np

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

    assignments = np.zeros(3, dtype=np.int)
    samples = 0

    stream = load_json_stream(open(args.dumps))
    for i in xrange(burnin):
        stream.next()
    for dump in stream:
        assignments += dump["assignments_summary"]
        samples += 1

    assignments = fix_order(assignments)
    _sum = float(sum(assignments))
    sys.stdout.write("%d samples\n" % samples)
    sys.stdout.write("%f\t%f\t%f\n" % (assignments[0] / _sum, assignments[1] / _sum, assignments[2] / _sum))

if __name__ == "__main__":
    main()
