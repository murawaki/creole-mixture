# -*- coding: utf-8 -*-
import sys, os
from argparse import ArgumentParser
from sklearn.decomposition import PCA
from scipy.stats import gaussian_kde
import numpy as np

sys.path.insert(1, os.path.join(sys.path[0], os.path.pardir))
from json_utils import load_json_file, load_json_stream

def extract_mat(langs):
    # if full == False: only leaves are extracted
    size = len(langs[0]["bin"])
    mat = np.empty((len(langs), size), dtype=np.int32)
    for i, lang in enumerate(langs):
        mat[i] = map(lambda x: int(x), lang["bin"])
    return mat

def do_pca(X):
    pca = PCA()
    U, S, V = pca._fit(X)
    X_transformed = np.dot(X - pca.mean_, pca.components_.T)
    return pca, X_transformed

def do_pca_new(pca, X):
    return np.dot(X - pca.mean_, pca.components_.T)

def plot_langs(langs, X_transformed, plt, p1, p2, plot_type=0):
    for i, lang in enumerate(langs):
        x, y = X_transformed[i, p1], X_transformed[i, p2]
        if lang["source"] == "APiCS":
            if plot_type in (0, 1):
                c = "r"
                # plt.annotate(lang["name"], (x, y),
                #              xytext=(x + 0.10, y + 0.05), size=8)
                plt.scatter(x, y, c=c, marker='s', s=30)
        else:
            if plot_type in (0, 2):
                c = "g"
                # plt.annotate(lang["name"], (x, y),
                #              xytext=(x + 0.10, y + 0.05), size=8)
                # print "%f\t%f\n" % (X_transformed[i, p1], X_transformed[i, p2])
                # if lang["name"] == "Japanese":
                #     plt.annotate(lang["name"], (x, y),
                #                  xytext=(x + 0.02, y + 0.02))
                plt.scatter(x, y, c=c, marker='o', s=30)

def main():
    parser = ArgumentParser()
    parser.add_argument("--plot_type", dest="plot_type", metavar="INT", type=int, default=0)
    parser.add_argument("--pc1", dest="pc1", metavar="INT", type=int, default=0)
    parser.add_argument("--pc2", dest="pc2", metavar="INT", type=int, default=1)
    parser.add_argument("--kde", dest="do_kde", action="store_true", default=False)
    parser.add_argument("--output", metavar="IMG", default=None)
    parser.add_argument("langs", metavar="LANG", default=None)
    args = parser.parse_args()

    langs = list(load_json_stream(open(args.langs)))
    # flist = load_json_file(sys.argv[2])
    dims = len(langs[0]["bin"])

    X = extract_mat(langs)
    pca, X_transformed = do_pca(X)

    import matplotlib.pyplot as plt
    plt.figure(figsize=(8, 6), dpi=120)

    # import matplotlib as mpl
    # mpl.rcParams['font.family'] = 'Nimbus Roman No9 L'
    import matplotlib.font_manager as font_manager
    path = '/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf'
    fontprop = font_manager.FontProperties(fname=path)

    p1, p2 = args.pc1, args.pc2  # first and second PCs (zero-based numbering)
    plot_type = args.plot_type # 0: both, 1: creole, 2: non-creole, 3: none
    # plt.xlim((-5, 4))
    # plt.ylim((-4, 3))
    plt.xlim((-4, 4))
    plt.ylim((-4, 4))
    plt.xticks(range(-4, 5), fontproperties=fontprop, size="25")
    plt.yticks(range(-4, 5), fontproperties=fontprop, size="25")

    plt.xlabel("PC%d (%2.1f%%)" % (p1 + 1, pca.explained_variance_ratio_[p1] * 100), fontproperties=fontprop, size="25")
    plt.ylabel("PC%d (%2.1f%%)" % (p2 + 1, pca.explained_variance_ratio_[p2] * 100), fontproperties=fontprop, size="25")
    plot_langs(langs, X_transformed, plt, p1, p2, plot_type=plot_type)
    plt.legend()

    if args.do_kde:
        val = []
        for i, lang in enumerate(langs):
            x, y = X_transformed[i, p1], X_transformed[i, p2]
            if plot_type == 1 and lang["source"] == "APiCS":
                val.append((x, y))
            elif plot_type == 2 and lang["source"] == "WALS":
                val.append((x, y))
        val = np.array(val).T
        # val = np.vstack((X_transformed[:, p1], X_transformed[:, p2]))
        kernel = gaussian_kde(val)
        xmin, xmax = plt.xlim()
        ymin, ymax = plt.ylim()
        _X, _Y = np.mgrid[xmin:xmax:100j, ymin:ymax:100j]
        positions = np.vstack([_X.ravel(), _Y.ravel()])
        Z = np.reshape(kernel(positions).T, _X.shape)
        # http://matplotlib.org/users/colormaps.html
        plt.imshow(np.rot90(Z), cmap=plt.cm.gist_earth_r, extent=[xmin, xmax, ymin, ymax])
        # plt.imshow(np.rot90(Z), cmap=plt.cm.hot_r, extent=[xmin, xmax, ymin, ymax])
        # plt.imshow(np.rot90(Z), cmap=plt.cm.afmhot_r, extent=[xmin, xmax, ymin, ymax])


    # plt.title('PCA')

    # plt.xlim([-2.5, 1.5])
    # plt.ylim([-1.5, 2.5])

    if args.output:
        plt.savefig(args.output, format="pdf", transparent=False, bbox_inches="tight")
        # plt.savefig(args.output, format="png", transparent=False, dpi=160)
    plt.show()


if __name__ == "__main__":
    main()
