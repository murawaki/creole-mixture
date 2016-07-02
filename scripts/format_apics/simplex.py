#
# plot model parameters on a simplex
#
import sys, os
from argparse import ArgumentParser
import codecs
import numpy as np
from scipy.misc import logsumexp
from scipy.stats import gaussian_kde
import matplotlib.pyplot as plt
from matplotlib.tri import UniformTriRefiner, Triangulation

sys.path.insert(1, os.path.join(sys.path[0], os.path.pardir))
from json_utils import load_json_file, load_json_stream

# import matplotlib as mpl
# mpl.rcParams['font.family'] = 'Nimbus Roman No9 L'
import matplotlib.font_manager as font_manager
path = '/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf'
fontprop = font_manager.FontProperties(fname=path)

corners = np.array([[0, 0], [1, 0], [0.5, 0.75**0.5]])
# Mid-points of triangle sides opposite of each corner
midpoints = [(corners[(i + 1) % 3] + corners[(i + 2) % 3]) / 2.0 \
             for i in range(3)]

def init_simplex(plt, subdiv=8, fsize=20):
    triangle = Triangulation(corners[:, 0], corners[:, 1])

    refiner = UniformTriRefiner(triangle)
    trimesh = refiner.refine_triangulation(subdiv=subdiv)

    plt.triplot(triangle) # plot triangle
    plt.axis('off')  # no normal axis
    plt.axis('equal')

    plt.annotate('L', (0, 0), xytext=(-0.08, -0.03), size=fsize, fontproperties=fontprop)
    plt.annotate('S', (1, 0), xytext=(1.02, -0.03), size=fsize, fontproperties=fontprop)
    plt.annotate('R', (0.5, 0.75**0.5), xytext=(0.47, 0.75**0.5 + 0.02), size=fsize, fontproperties=fontprop)

    # xy1 = abc2xy(np.array([1, 0, 0]))
    # plt.scatter(xy1[0], xy1[1], c='green', marker='o', s=30)
    return trimesh

def fix_order(abc):
    # NOTE: data order: R, L, S  and  plot order L, S, R
    return np.array([abc[1], abc[2], abc[0]])

def abc2xy(abc):
    # Init to triangle centroid
    x = 1.0 / 2
    y = 1.0 / (2 * np.sqrt(3))
    x = x - (1.0 / np.sqrt(3)) * abc[0] * np.cos(np.pi / 6)
    y = y - (1.0 / np.sqrt(3)) * abc[0] * np.sin(np.pi / 6)
    # Vector 2 - bisect out of lower right vertex  
    x = x + (1.0 / np.sqrt(3)) * abc[1] * np.cos(np.pi / 6)
    y = y - (1.0 / np.sqrt(3)) * abc[1] * np.sin(np.pi / 6)        
    # Vector 3 - bisect out of top vertex
    y = y + (1.0 / np.sqrt(3) * abc[2])
    return np.array((x, y))

def xy2bc(xy, tol=1.e-3):
    '''Converts 2D Cartesian coordinates to barycentric.'''
    s = [(corners[i] - midpoints[i]).dot(xy - midpoints[i]) / 0.75 \
         for i in range(3)]
    return np.clip(s, tol, 1.0 - tol)


def main():
    parser = ArgumentParser()
    parser.add_argument("--mtype", metavar="MODEL_TYPE", default="mono")
    parser.add_argument("--type", metavar="POINT_TYPE", default="theta")
    parser.add_argument("--output", metavar="IMG", default=None)
    parser.add_argument("dumps", metavar="LANG", default=None)
    args = parser.parse_args()

    fsize=36
    subdiv=8
    burnin = 100

    plt.figure(figsize=(8, 6), dpi=120)
    trimesh = init_simplex(plt, fsize=fsize, subdiv=8)

    points = []
    stream = load_json_stream(open(args.dumps))
    for i in xrange(burnin):
        stream.next()
    for dump in stream:
        N = len(dump['mixlist']) # number of langs

        if args.mtype == 'mono':
            for lang in dump['mixlist']:
                adist = lang["adist"]
                _sum = adist["K"] * adist["alpha"] + sum(adist["voc"])
                probs = []
                for k in xrange(adist["K"]):
                    probs.append((adist["voc"][k] + adist["alpha"]) / _sum)
                probs2 = fix_order(probs)
                points.append(probs2)
                xy = abc2xy(probs2)
                plt.scatter(xy[0], xy[1], c='green', marker='s', s=60)
        elif args.mtype == 'fact':
            J = len(dump['mus']) # number of features
            if args.type == "feature":
                for j, mu in enumerate(dump['mus']):
                    _sum = logsumexp(mu)
                    probs = np.exp(mu - _sum)
                    probs2 = fix_order(probs)
                    points.append(probs2)
                    xy = abc2xy(probs2)
                    plt.scatter(xy[0], xy[1], c='blue', marker='o', s=60)
            else:
                for creole in dump['mixlist']:
                    etas = np.array(creole['etas'])
                    if args.type == "theta":
                        for j in xrange(J):
                            fcts = np.zeros(3)
                            for k in xrange(3):
                                fcts[k] = dump['mus'][j][k] + etas[k]
                            _sum = logsumexp(fcts)
                            probs = np.exp(fcts - _sum)
                            probs2 = fix_order(probs)
                            points.append(probs2)
                            xy = abc2xy(probs2)
                            plt.scatter(xy[0], xy[1], c='red', marker='.', s=60)
                    elif args.type == "lang":
                        _sum = logsumexp(etas)
                        probs = np.exp(etas - _sum)
                        probs2 = fix_order(probs)
                        points.append(probs2)
                        xy = abc2xy(probs2)
                        plt.scatter(xy[0], xy[1], c='green', marker='s', s=60)

    if args.output:
        plt.savefig(args.output, format="pdf", transparent=False, bbox_inches="tight")
        # plt.savefig(args.output, format="png", transparent=False, dpi=160)

    plt.show()


if __name__ == "__main__":
    main()
