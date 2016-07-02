# -*- coding: utf-8 -*-

import sys
import codecs
import json
import math
import numpy as np
from scipy.misc import logsumexp
from scipy.stats import norm, laplace # gamma
from scipy.special import gammaln, multigammaln
import random # for debug
from argparse import ArgumentParser

from json_utils import load_json_file, load_json_stream
from rand_utils import rand_partition, rand_partition_log
from dirichlet import DirichletDistribution, DirichletDistributionGammaPrior, KUniformDistribution, KDirichletProcess

class CreoleMixtureDiscrete(object):
    SAMPLE_HYPER = 1
    SAMPLE_ASSIGNMENT = 2
    UNIV = 0
    LEX = 1
    SUB = 2

    def __init__(self, fid2struct, alpha_a=0.1, alpha_u=1.0):
        self.fid2struct = fid2struct
        self.dims = len(self.fid2struct)
        self.alpha_a = alpha_a
        self.alpha_u = alpha_u

        self.mixlist = []
        self.operators = []
        self.adists = []
        # self.adist = DirichletDistribution(3, alpha=alpha_a)
        self.operators.append((self.SAMPLE_HYPER, self.adists))
        self.udists = []
        self.operators.append((self.SAMPLE_HYPER, self.udists))
        for i in xrange(self.dims):
            udist = DirichletDistributionGammaPrior(len(self.fid2struct[i]["vid2label"]), alpha=self.alpha_u)
            self.udists.append(udist)

    def add_mix(self, creole, lexifier, substrate, langname=None):
        obj = {
            "creole": creole,
            "lexifier": lexifier,
            "substrate": substrate,
            "assignments": np.zeros(self.dims, dtype=np.int32),
            "adist": DirichletDistributionGammaPrior(3, alpha=self.alpha_a),
        }
        if langname:
            obj["langname"] = langname
        self.mixlist.append(obj)
        self.adists.append(obj["adist"])
        for i in xrange(self.dims):
            self.operators.append((self.SAMPLE_ASSIGNMENT, (obj, i)))
        return obj

    def log_marginal(self):
        ll = 0.0
        # ll = self.adist.log_marginal()
        for udist in self.udists:
            ll += udist.log_marginal()
        for obj in self.mixlist:
            ll += obj["adist"].log_marginal()
        return ll

    def init_mcmc(self):
        for obj in self.mixlist:
            for i in xrange(self.dims):
                cands = []
                cv = obj["creole"][i]
                if cv == obj["lexifier"][i]:
                    cands.append(self.LEX)
                if cv == obj["substrate"][i]:
                    cands.append(self.SUB)
                if len(cands) <= 0:
                    a = self.UNIV
                else:
                    if len(cands) > 1:
                        r = rand_partition(np.ones(len(cands)))
                    else:
                        r = 0
                    a = cands[r]
                obj["assignments"][i] = a
                # self.adist.add(a)
                obj["adist"].add(a)
                if a == self.UNIV:
                    self.udists[i].add(cv)

    def _check_assignments(self):
        pass
        # # DEBUG
        # assignments = np.zeros(3)
        # for obj in self.mixlist:
        #     for i in obj["assignments"]:
        #         assignments[i] += 1
        # print assignments
        # print self.adist.voc
        # assert(np.all(np.equal(assignments, self.adist.voc)))

    def sample(self, temp=1.0):
        random.shuffle(self.operators)
        c_count = [0, 0]
        for _op, struct in self.operators:
            if _op == self.SAMPLE_HYPER:
                # pass
                self.sample_hyper(struct)
            else:
                rv = self.sample_assignment(struct[0], struct[1], temp=temp)
                c_count[rv] += 1
        # sys.stderr.write("change rate: %f\n" % (c_count[1] / float(sum(c_count))))
        # sys.stderr.write("eta accept rate: %f\n" % (eta_count[1] / float(sum(eta_count))))

    def sample_hyper(self, dists):
        for dist in dists:
            dist.sample_hyper()
        # alpha = dists[0].sample_hyper_tied(dists[0].alpha, dists)
        # for dist in dists:
        #     dist.alpha = alpha

    def sample_assignment(self, obj, i, temp=1.0):
        cv = obj["creole"][i]
        a = obj["assignments"][i]
        obj["adist"].remove(a)
        # self.adist.remove(a)
        if a == self.UNIV:
            self.udists[i].remove(cv)
        probs = []
        cands = []
        if cv == obj["lexifier"][i]:
            probs.append(obj["adist"].voc[self.LEX] + obj["adist"].alpha)
            cands.append(self.LEX)
        if cv == obj["substrate"][i]:
            probs.append(obj["adist"].voc[self.SUB] + obj["adist"].alpha)
            cands.append(self.SUB)
        if len(cands) > 0:
            probs.append((obj["adist"].voc[self.UNIV] + obj["adist"].alpha) \
                         * self.udists[i].prob(cv))
            cands.append(self.UNIV)
            if not temp == 1.0:
                s = sum(probs)
                for idx, p in enumerate(probs):
                    probs[idx] = (p/s) ** (1.0/temp)
            r = rand_partition(probs)
            a2 = cands[r]
        else:
            a2 = self.UNIV
        obj["assignments"][i] = a2
        # self.adist.add(a2)
        obj["adist"].add(a2)
        if a2 == self.UNIV:
            self.udists[i].add(cv)
        return False if a == a2 else True

    def serialize(self, _iter=0):
        obj = {
            "iter": _iter,
            # "adist": self.adist.dump(),
            "udists": [],
            "mixlist": [],
        }
        for udist in self.udists:
            obj["udists"].append(udist.dump())
        summary = np.zeros(3, dtype=np.int32)
        for obj2 in self.mixlist:
            obj["mixlist"].append({
                "assignments": obj2["assignments"].tolist(),
                "adist": obj2["adist"].dump(),
            })
            if "langname" in obj2:
                obj["mixlist"][-1]["langname"] = obj2["langname"]
            for k in obj2["assignments"]:
                summary[k] += 1
        obj["assignments_summary"] = summary.tolist()
        return json.dumps(obj)


class CreoleMixtureDiscreteFactored(CreoleMixtureDiscrete):
    SAMPLE_ETA = 3
    SAMPLE_MU = 4

    def __init__(self, fid2struct, gamma_f=1.0, gamma_c=1.0, alpha_u=1.0):
        self.fid2struct = fid2struct
        self.dims = len(self.fid2struct)
        self.gamma_f = gamma_f
        self.gamma_c = gamma_c
        self.alpha_u = alpha_u

        self.mixlist = []
        self.operators = []
        self.udists = []
        self.operators.append((self.SAMPLE_HYPER, self.udists))
        self.mus = np.empty((self.dims, 3))
        for j in xrange(self.dims):
            udist = DirichletDistribution(len(self.fid2struct[j]["vid2label"]), alpha=self.alpha_u)
            self.udists.append(udist)
            for k in xrange(3):
                self.mus[j,k] = np.random.laplace(scale=self.gamma_f) # np.random.normal(0, self.sigmas[j,k] ** 0.5)
                self.operators.append((self.SAMPLE_MU, (j, k)))

    def add_mix(self, creole, lexifier, substrate, langname=None):
        obj = {
            "creole": creole,
            "lexifier": lexifier,
            "substrate": substrate,
            "etas": np.empty(3),
            "logthetas": np.empty((self.dims, 3)),
            "assignments": np.zeros(self.dims, dtype=np.int32),
            "ready": np.zeros(self.dims, dtype=np.bool),
        }
        if langname:
            obj["langname"] = langname
        self.mixlist.append(obj)
        for i in xrange(self.dims):
            self.operators.append((self.SAMPLE_ASSIGNMENT, (obj, i)))
        obj["etas"] = np.random.laplace(scale=self.gamma_c, size=3) # np.random.normal(0, obj["taus"] ** 0.5, size=3)
        for k in xrange(3):
            self.operators.append((self.SAMPLE_ETA, (obj, k)))
        return obj

    def _calc_theta(self, obj, j):
        a = obj["etas"] + self.mus[j]
        _sum = logsumexp(a)
        obj["logthetas"][j] = a - _sum
        obj["ready"][j] = True

    def log_marginal(self):
        ll = 0.0
        # ## exponential distributions, ignore fixed params
        # ll -= self.gamma_f * self.sigmas.sum()
        # ## normal distributions
        # ll -= 0.5 * np.log(self.sigmas).sum() + ((self.mus ** 2) / (2.0 * self.sigmas)).sum()
        for j in xrange(self.dims):
            for k in xrange(3):
                ll += np.log(laplace.pdf(self.mus[j,k], scale=self.gamma_f))
        for udist in self.udists:
            ll += udist.log_marginal()
        for obj in self.mixlist:
            # ll -= self.gamma_c * obj["taus"].sum()
            # ll -= 0.5 * np.log(obj["taus"]).sum() + ((obj["etas"] ** 2) / (2.0 * obj["taus"])).sum()
            for k in xrange(3):
                ll += np.log(laplace.pdf(obj["etas"][k], scale=self.gamma_c))
            for j in xrange(self.dims):
                if obj["ready"][j] == False:
                    self._calc_theta(obj, j)
                k = obj["assignments"][j]
                ll += obj["logthetas"][j,k]
        return ll

    def init_mcmc(self):
        for obj in self.mixlist:
            for i in xrange(self.dims):
                cands = []
                cv = obj["creole"][i]
                if cv == obj["lexifier"][i]:
                    cands.append(self.LEX)
                if cv == obj["substrate"][i]:
                    cands.append(self.SUB)
                if len(cands) <= 0:
                    a = self.UNIV
                else:
                    if len(cands) > 1:
                        r = rand_partition(np.ones(len(cands)))
                    else:
                        r = 0
                    a = cands[r]
                obj["assignments"][i] = a
                if a == self.UNIV:
                    self.udists[i].add(cv)

    def sample(self, temp=1.0):
        random.shuffle(self.operators)
        c_count = [0, 0]
        eta_count = [0, 0]
        mu_count = [0, 0]
        for _op, struct in self.operators:
            if _op == self.SAMPLE_HYPER:
                # pass
                self.sample_hyper(struct)
            elif _op == self.SAMPLE_ASSIGNMENT:
                rv = self.sample_assignment(struct[0], struct[1], temp=temp)
                c_count[rv] += 1
            # elif _op == self.SAMPLE_TAU:
            #     self.sample_tau(struct[0], struct[1])
            # elif _op == self.SAMPLE_SIGMA:
            #     self.sample_sigma(struct[0], struct[1])
            elif _op == self.SAMPLE_ETA:
                rv = self.sample_eta(struct[0], struct[1])
                eta_count[rv] += 1
            elif _op == self.SAMPLE_MU: 
                rv = self.sample_mu(struct[0], struct[1])
                mu_count[rv] += 1
            else:
                exit(1)
        sys.stderr.write("change rate: %f\n" % (c_count[1] / float(sum(c_count))))
        sys.stderr.write("eta accept rate: %f\n" % (eta_count[1] / float(sum(eta_count))))
        sys.stderr.write("mu accept rate:  %f\n" % (mu_count[1] / float(sum(mu_count))))

    def sample_assignment(self, obj, j, temp=1.0):
        cv = obj["creole"][j]
        k = obj["assignments"][j]
        if k == self.UNIV:
            self.udists[j].remove(cv)
        if obj["ready"][j] == False:
            self._calc_theta(obj, j)
        probs = []
        cands = []
        if cv == obj["lexifier"][j]:
            probs.append(np.exp(obj["logthetas"][j,self.LEX]))
            cands.append(self.LEX)
        if cv == obj["substrate"][j]:
            probs.append(np.exp(obj["logthetas"][j,self.SUB]))
            cands.append(self.SUB)
        if len(cands) > 0:
            probs.append(np.exp(obj["logthetas"][j,self.UNIV]) * self.udists[j].prob(cv))
            cands.append(self.UNIV)
            if not temp == 1.0:
                s = sum(probs)
                for idx, p in enumerate(probs):
                    probs[idx] = (p/s) ** (1.0/temp)
            r = rand_partition(probs)
            k2 = cands[r]
        else:
            k2 = self.UNIV
        obj["assignments"][j] = k2
        if k2 == self.UNIV:
            self.udists[j].add(cv)
        return False if k == k2 else True

    def sample_eta(self, obj, k, scale=5.0):
        current = obj["etas"][k]
        proposal = np.random.normal(current, scale)
        current_logp = np.log(laplace.pdf(current, scale=self.gamma_c))
        proposal_logp = np.log(laplace.pdf(proposal, scale=self.gamma_c))
        # current_logp = -1 * ((current * current) / (2.0 * obj["taus"][k]))
        # proposal_logp = -1 * ((proposal * proposal) / (2.0 * obj["taus"][k]))
        for j in xrange(self.dims):
            if obj["ready"][j] == False:
                self._calc_theta(obj, j)
            k2 = obj["assignments"][j]
            current_logp += obj["logthetas"][j,k2]
        theta_old = obj["logthetas"].copy()
        obj["etas"][k] = proposal
        for j in xrange(self.dims):
            self._calc_theta(obj, j)
            k2 = obj["assignments"][j]
            proposal_logp += obj["logthetas"][j,k2]
        if current_logp > proposal_logp and rand_partition_log([current_logp, proposal_logp]) == 0:
            # rejected, undoing changes
            obj["etas"][k] = current
            # do not entirely override obj["logthetas"] because it is pointed from elsewhere
            for j in xrange(self.dims):
                obj["logthetas"][j] = theta_old[j]
            return False
        else:
            # accepted
            return True

    def sample_mu(self, j, k, scale=5.0):
        current = self.mus[j,k]
        proposal = np.random.normal(current, scale)
        current_logp = np.log(laplace.pdf(current, scale=self.gamma_f))
        proposal_logp = np.log(laplace.pdf(proposal, scale=self.gamma_f))
        # current_logp = -1 * ((current * current) / (2.0 * self.sigmas[j,k]))
        # proposal_logp = -1 * ((proposal * proposal) / (2.0 * self.sigmas[j,k]))
        theta_olds = []
        for obj in self.mixlist:
            if obj["ready"][j] == False:
                self._calc_theta(obj, j)
            k2 = obj["assignments"][j]
            current_logp += obj["logthetas"][j,k2]
            theta_olds.append(obj["logthetas"][j].copy())
        self.mus[j,k] = proposal
        for obj in self.mixlist:
            self._calc_theta(obj, j)
            k2 = obj["assignments"][j]
            proposal_logp += obj["logthetas"][j,k2]
        if current_logp > proposal_logp and rand_partition_log([current_logp, proposal_logp]) == 0:
            # rejected, undoing changes
            self.mus[j,k] = current
            for obj, theta_old in zip(self.mixlist, theta_olds):
                obj["logthetas"][j] = theta_old
            return False
        else:
            # accepted
            return True

    def serialize(self, _iter=0):
        obj = {
            "iter": _iter,
            "udists": [],
            # "sigmas": self.sigmas.tolist(),
            "mus": self.mus.tolist(),
            "mixlist": [],
        }
        for udist in self.udists:
            obj["udists"].append(udist.dump())
        summary = np.zeros(3, dtype=np.int32)
        for obj2 in self.mixlist:
            obj["mixlist"].append({
                # "taus": obj2["taus"].tolist(),
                "etas": obj2["etas"].tolist(),
                "assignments": obj2["assignments"].tolist(),
            })
            if "langname" in obj2:
                obj["mixlist"][-1]["langname"] = obj2["langname"]
            for k in obj2["assignments"]:
                summary[k] += 1
        obj["assignments_summary"] = summary.tolist()
        return json.dumps(obj)


def main():
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr)

    parser = ArgumentParser()
    parser.add_argument("-s", "--seed", dest="seed", metavar="INT", type=int, default=None,
                        help="random seed")
    parser.add_argument("-i", "--iter", dest="_iter", metavar="INT", type=int, default=20000,
                        help="number of dimensions")
    parser.add_argument("-t", "--type", dest="mtype", metavar="MODEL_TYPE", default="mono",
                        help="model type (mono or fact)")
    parser.add_argument("--dump", default=None)
    parser.add_argument("langs", metavar="LANG", default=None)
    # parser.add_argument("fid2struct", metavar="FLIST", default=None)
    parser.add_argument("flist", metavar="FLIST", default=None)
    parser.add_argument("sources", metavar="SOURCES", default=None)
    args = parser.parse_args()

    if args.seed is not None:
        np.random.seed(args.seed)
        random.seed(args.seed)

    creoles = {}
    with codecs.getreader("utf-8")(open(args.sources)) as f:
        for line in f:
            line = line.rstrip()
            creole, lexifier, substrate = line.split("\t")
            creoles[creole] = {
                "lexifier": lexifier,
                "substrate": substrate,
            }
    langs = {}
    for lang in load_json_stream(open(args.langs)):
        if lang["source"] == "APiCS":
            langs[lang["name"]] = lang
        else:
            langs[lang["wals_code"]] = lang

    fid2struct = load_json_file(args.flist)

    # **TODO** pass command-line args
    if args.mtype == 'mono':
        cm = CreoleMixtureDiscrete(fid2struct, alpha_a=1.0, alpha_u=1.0)
    elif args.mtype == 'fact':
        cm = CreoleMixtureDiscreteFactored(fid2struct, gamma_f=10.0, gamma_c=10.0, alpha_u=1.0)
    else:
        sys.stderr.write("unsupported model\n")
        exit(1)

    objs = []
    for creole, obj in creoles.iteritems():
        if creole not in langs:
            sys.stderr.write("creole %s not found in the lang list\n" % creole)
            continue
        clang = langs[creole]
        if obj["lexifier"] not in langs:
            sys.stderr.write("lexifier %s not found in the lang list\n" % obj["lexifier"])
            continue
        llang = langs[obj["lexifier"]]
        if obj["substrate"] not in langs:
            sys.stderr.write("substrate %s not found in the lang list\n" % obj["substrate"])
            continue
        slang = langs[obj["substrate"]]
        clang_cat = clang["catvect_filled"]
        llang_cat = llang["catvect_filled"]
        slang_cat = slang["catvect_filled"]
        obj = cm.add_mix(clang_cat, llang_cat, slang_cat, langname=creole)
        objs.append({
            "obj": obj,
            # "creole": evaluator.cat2bin(np.array(clang["catvect_filled"])),
            # "lexifier": evaluator.cat2bin(np.array(llang["catvect_filled"])),
            # "substrate": evaluator.cat2bin(np.array(slang["catvect_filled"])),
        })

    sys.stderr.write("%d creoles\n" % len(cm.mixlist))

    cm.init_mcmc()
    sys.stderr.write("0\tlog marginal: %f\n" % cm.log_marginal())
    # print cm.niw.L
    sys.stdout.write("%s\n" % cm.serialize(_iter=0))
    temp = 2.0
    tempstep = temp / (args._iter * 0.75)
    for _iter in xrange(args._iter):
        temp -= tempstep
        if temp <= 0.1:
            temp = 0.1
        # print >>sys.stderr, temp
        # cm.sample(temp=temp)
        cm.sample(temp=1.0)

        sys.stderr.write("%d\tlog marginal: %f\n" % (_iter + 1, cm.log_marginal()))
        if (_iter + 1) % 100 == 0:
            sys.stdout.write("%s\n" % cm.serialize(_iter=_iter + 1))
            # print cm.niw.L

    if args.dump:
        if args.dump == "-":
            f = codecs.getwriter("utf-8")(sys.stdout)
        else:
            f = codecs.getwriter("utf-8")(open(args.dump, "w"))
        rv = []
        for obj_base in objs:
            obj = obj_base["obj"]
            rv.append({
                "creole": obj["creole"],
                "lexifier": obj["lexifier"],
                "substrate": obj["substrate"],
                "assignments": obj["assignments"].tolist(),
            })
        f.write("%s\n" % json.dumps(rv))
        f.close()

if __name__ == "__main__":
    main()
