# -*- coding: utf-8 -*-
import sys, os
import codecs
import json
from argparse import ArgumentParser
from collections import defaultdict

sys.path.insert(1, os.path.join(sys.path[0], os.path.pardir))
from csv_utils import UnicodeReader

def parse_csv(fname, keys, pk, to_int=[], nonnull=[]):
    csv = UnicodeReader(open(fname, 'rb'))
    key2id = {}
    for i, k in enumerate(keys):
        key2id[k] = i
    csv.next()  # skip the first line
    dic = {}
    for row in csv:
        skip = False
        for k in nonnull:
            if len(row[key2id[k]]) <= 0:
                skip = True
                break
        if skip:
            continue
        for k in to_int:
            if len(row[key2id[k]]) > 0:
                row[key2id[k]] = int(row[key2id[k]])
        l = row[key2id[pk]]
        dic[l] = {}
        for k in keys:
            if key2id[k] < len(row):
                dic[l][k] = row[key2id[k]]
            else:
                sys.stderr.write(u"key out of range: '%s' for %s\n" % (k, row))
    return dic

def table2listdict(table, k):
    rv = {}
    for v in table.itervalues():
        if v[k] not in rv:
            rv[v[k]] = []
        rv[v[k]].append(v)
    return rv

def main():
    parser = ArgumentParser()
    parser.add_argument("basedir", metavar="LANG", default=None)
    parser.add_argument("langs", metavar="LANGS", help="raw languages")
    parser.add_argument("flist", metavar="FLIST", help="APiCS features")
    args = parser.parse_args()

    features = parse_csv("%s/feature.csv" % (args.basedir),
                         ["pk", "feature_type", "multivalued", "wals_id", "wals_representation", "representation", "area"],
                         "pk",
                         to_int=["pk", "wals_id"],
                         nonnull=["wals_id"])
    languages = parse_csv("%s/language.csv" % (args.basedir),
                          ["pk", "jsondata", "polymorphic_type", "id", "name", "description", "markup_description", "latitude", "longitude", "updated", "active", "created", "version"],
                          "pk",
                          to_int=["pk", "id"])
    lects = parse_csv("%s/lect.csv" % (args.basedir),
                      ["pk", "region", "lexifier", "language_pk"],
                      "pk",
                      to_int=["pk", "language_pk"])

    languageidentifiers = parse_csv("%s/languageidentifier.csv" % (args.basedir),
                                    ["pk", "jsondata", "language_pk", "identifier_pk", "description", "updated", "active", "created", "version"],
                                    "pk",
                                    to_int=["pk", "language_pk", "identifier_pk"])
    identifiers = parse_csv("%s/identifier.csv" % (args.basedir),
                            ["pk", "jsondata", "name", "description", "markup_description", "id", "type", "lang", "updated", "active", "created", "version"],
                            "pk",
                            to_int=["pk"])

    valuesets = parse_csv("%s/valueset.csv" % (args.basedir),
                          ["pk", "jsondata", "polymorphic_type", "id", "description", "markup_description", "language_pk", "parameter_pk", "contribution_pk", "source", "updated", "active", "created", "version"],
                          "pk",
                          to_int=["pk", "language_pk", "parameter_pk", "contribution_pk"])
    values = parse_csv("%s/value.csv" % (args.basedir),
                       ["jsondata", "polymorphic_type", "id", "name", "description", "markup_description", "pk", "valueset_pk", "domainelement_pk", "frequency", "confidence", "updated", "active", "created", "version"],
                       "pk",
                       to_int=["pk", "valueset_pk", "domainelement_pk"])
    domainelements = parse_csv("%s/domainelement.csv" % (args.basedir),
                               ["pk", "jsondata", "polymorphic_type", "id", "name", "description", "markup_description", "parameter_pk", "number", "abbr", "updated", "active", "created", "version"],
                               "pk",
                               to_int=["pk", "parameter_pk", "number"])
    parameters = parse_csv("%s/parameter.csv" % (args.basedir),
                           ["pk", "jsondata", "polymorphic_type", "id", "name", "description", "markup_description", "updated", "active", "created", "version"],
                           "pk",
                           to_int=["pk", "id"])

    language2identifiers = table2listdict(languageidentifiers, "language_pk")
    language2lects = table2listdict(lects, "language_pk")

    language2struct = {}
    for language in languages.itervalues():
        out = {}
        for k in ("name", "latitude", "longitude"):
            if k in language:
                out[k] = language[k]
        if language["pk"] in language2identifiers:
            ids = []
            for languageidentifier in language2identifiers[language["pk"]]:
                identifier = identifiers[languageidentifier["identifier_pk"]]
                ids.append({
                    "type": identifier["type"],
                    "name": identifier["name"],
                })
            out["identifiers"] = ids
        if language["pk"] in language2lects:
            ls = []
            for lect in language2lects[language["pk"]]:
                ls.append({
                    "region": lect["region"],
                    "lexifier": lect["lexifier"],
                })
        language2struct[language["pk"]] = out

    apics_features = {}
    for domainelement_pk, domainelement in domainelements.iteritems():
        apics_id = domainelement["id"].split("-")[0]
        apics_id = int(apics_id) - 1
        if apics_id < 0:
            continue
        apics_vid = domainelement["number"] - 1
        parameter = parameters[domainelement["parameter_pk"]]
        if apics_id not in apics_features:
            apics_features[apics_id] = {
                "name": parameter["name"],
                "idx": apics_id,
                "fid": apics_id,
                "label2vid": {},
                "vid2label": {},
            }
        else:
            assert(apics_features[apics_id]["name"] == parameter["name"])
        if domainelement["name"] not in apics_features[apics_id]["label2vid"]:
            apics_features[apics_id]["label2vid"][domainelement["name"]] = apics_vid
            apics_features[apics_id]["vid2label"][apics_vid] = domainelement["name"]
        else:
            assert(apics_features[apics_id]["label2vid"][domainelement["name"]] == apics_vid)
    for feature_pk, feature in features.iteritems():
        apics_id = feature_pk - 2 # HACK
        if apics_id < 0:
            continue
        if apics_id in apics_features:
            fstruct = apics_features[apics_id]
            fstruct["feature_type"] = feature["feature_type"]
            fstruct["area"] = feature["area"]
            if "wals_id" in feature:
                fstruct["wals_id"] = ("%dA" % feature["wals_id"])
        else:
            sys.stderr.write("No corresponding feature defined: %s\n" % apics_id)

    language2count = defaultdict(int)
    langfeatures = []
    for value_pk, value in values.iteritems():
        valueset = valuesets[value["valueset_pk"]]
        # if valueset["parameter_pk"] not in parameters:
        #     continue
        # parameter = parameters[valueset["parameter_pk"]]
        language = languages[valueset["language_pk"]]
        domainelement = domainelements[value["domainelement_pk"]]
        parameter = parameters[domainelement["parameter_pk"]]

        language2count[language["pk"]] += 1

        # print language
        # print value
        # print value_struct
        # print valueset
        # print feature
        # print domainelement

        apics_id = parameter["id"] - 1
        if apics_id < 0: # ???
            continue
        apics_vid = domainelement["number"] - 1

        out = {
            "lang": language["name"],
            "apics_id": apics_id,
            "fname": parameter["name"],
            "valname": domainelement["name"],
            "apics_vid": apics_vid,
            "confidence": value["confidence"],
            "frequency": float(value["frequency"]) / 100.0,
        }

        # if feature["wals_id"]:
        if "wals_id" in apics_features[apics_id]:
            out["wals_id"] = apics_features[apics_id]["wals_id"]
            # out["wals_id"] = ("%dA" % feature["wals_id"])

            valueset_json = json.loads(valueset["jsondata"])
            if "wals_value_number" in valueset_json:
                out["walsval"] = valueset_json["wals_value_number"]
            else:
                pass
                # No corresponding WALS feature value:
                # sys.stderr.write("WARNING: NO WALS FEATURE VALUE: %s:\t%s (%s) freq: %s\n" % (parameter["name"], domainelement["name"], domainelement["abbr"], value["frequency"]))
                # continue
        # fout.write("%s\n" % json.dumps(out))
        langfeatures.append(out)


    # filtering
    name2lang = {}
    for pk, lang in language2struct.iteritems():
        if language2count[pk] > 0:
            # lout.write("%s\n" % json.dumps(out))
            name2lang[lang["name"]] = lang
            lang["features"] = {}
            lang["apics_features"] = {}
            lang["source"] = "APiCS"
        else:
            sys.stderr.write("WARNING: NO FEATURE FOR LANGUAGE %s\n" % lang["name"])

    for langfeature in langfeatures:
        if langfeature["lang"] not in name2lang:
            sys.stderr.write("feature for an undefined lang: %s\n" % langfeature["lang"])
            continue
        lang = name2lang[langfeature["lang"]]

        if langfeature["apics_id"] in lang["apics_features"]:
            lang["apics_features"][langfeature["apics_id"]].append((langfeature["apics_vid"], langfeature["frequency"]))
        else:
            lang["apics_features"][langfeature["apics_id"]] = [(langfeature["apics_vid"], langfeature["frequency"])]

        if "walsval" in langfeature:
            wals_id = langfeature["wals_id"]
            walsval = langfeature["walsval"]
            v = float(langfeature["frequency"]) / 100.0
            if wals_id in lang["features"]:
                if not lang["features"][wals_id] == walsval - 1:
                    sys.stdwrr.write("inconsistent feature value: %d\t%d\n" % (lang["features"][wals_id], walsval - 1))
                # lang["features"][wals_id].append((walsval, v))
            else:
                lang["features"][wals_id] = walsval - 1
                # lang["features"][wals_id] = [(walsval, v)]

    with codecs.getwriter("utf-8")(open(args.langs, "w")) as f:
        for name, lang in name2lang.iteritems():
            f.write("%s\n" % json.dumps(lang))

    apics_features2 = []
    for i in xrange(len(apics_features)):
        fstruct = apics_features[i]
        vid2label2 = []
        for j in xrange(len(fstruct["vid2label"])):
            vid2label2.append(fstruct["vid2label"][j])
        fstruct["vid2label"] = vid2label2
        apics_features2.append(fstruct)
    apics_features = apics_features2
    with codecs.getwriter("utf-8")(open(args.flist, "w")) as f:
        f.write("%s\n" % json.dumps(apics_features))


if __name__ == "__main__":
    main()
