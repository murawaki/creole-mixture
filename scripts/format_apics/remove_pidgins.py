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
    parser.add_argument("langs_all", metavar="INPUT", default=None)
    parser.add_argument("flist", metavar="FLIST", default=None)
    parser.add_argument("langs", metavar="OUTPUT", default=None)
    args = parser.parse_args()

    fid2struct = load_json_file(args.flist)
    fsize = len(fid2struct)

    fname = "Ongoing creolization of pidgins"
    vnames = ["Not applicable (because the language is not a pidgin)", "Widespread"]

    fstruct = None
    for fstruct2 in fid2struct:
        if fstruct2["name"] == fname:
            fstruct = fstruct2
            break
    if not fstruct:
        sys.stderr.write("No such feature found\n")
        exit(1)
    vids = []
    for vname in vnames:
        if vname not in fstruct["label2vid"]:
            sys.stderr.write("No such feature value found\n")
            exit(1)
        vid = fstruct["label2vid"][vname]
        vids.append(vid)
    fid = str(fstruct["fid"])

    sys.stderr.write("fid, vid: %s %s\n" % (fid, vids))

    lang_total, lang_survived = 0, 0
    with codecs.getwriter("utf-8")(open(args.langs, "w")) as out:
        for lang in load_json_stream(open(args.langs_all)):
            lang_total += 1
            survived = True
            if lang["source"] == "APiCS":
                if fid in lang["apics_features"]:
                    if lang["apics_features"][fid][0][0] not in vids:
                        sys.stderr.write("remove %s (pidgins: %s)\n" % (lang["name"], lang["apics_features"][fid][0][0]))
                        survived = False
                else:
                    sys.stderr.write("keep %s (feature missed)\n" % lang["name"])
                    # survived = False
            if survived:
                lang_survived += 1
                out.write("%s\n" % json.dumps(lang))

    sys.stderr.write("language thresholding: %d -> %d\n" % (lang_total, lang_survived))


if __name__ == "__main__":
    main()
