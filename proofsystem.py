
from collections import defaultdict
import math
import numbers

import graphsort

from distribution import CallRef, DistrCall, Distribution, LiteralRef
from model import DistrResult, Model

import algprob

class ProofEnv(object):

  def __init__(self, model, timePenaltyRate):
    self.model = model
    self.timePenaltyRate = timePenaltyRate
    self.varValues = {}
    self.newVars = []
    self.labelPolys = {}

  def resolveValue(value):
    if isinstance(value, Variable):
      assert value.varid in self.varValues
      return self.varValues[value.varid]
    return value

  def resolveCall(call):
    assert isinstance(call, DistrCall)
    return DistrCall(call.function, map(self.resolveValue, call.parameters))

  def unify(self, proofValue, retValue):
    assert isinstance(retValue, LiteralRef)
    if isinstance(proofValue, Variable):
      varid = proofValue.varid
      if varid in self.varValues:
        varValue = self.varValues[varid]
        assert self.model.isEqual(varValue, retValue)
        self.model.modifyReferenceCount(retValue, -1)
      else:
        self.varValues[varid] = retValue
        self.newVars.append((proofValue, retValue))
    else:
      assert isinstance(proofValue, LiteralRef)
      assert self.model.isEqual(proofValue, retValue)

  def unifyCalls(self, proofCall, distrCall):
    assert proofCall.function == distrCall.function
    assert len(proofCall.parameters) == len(distrCall.parameters)
    for p,d in zip(proofCall.parameters, distrCall.parameters):
      self.unify(p, d)

  def popNewVars(self):
    newVars = self.newVars
    self.newVars = []
    return newVars

  def expandProofHelper(self, values, calls, rets, proof):
    resolve = lambda x: algprob.resolveValue(values, x)
    if len(calls) == 0:
      assert isinstance(proof, ResultProof)
      assert len(proof.result) == len(rets)
      rets = [resolveValue(values, r) for r in rets]
      for p,r in zip(proof.result, rets):
        self.unify(p, r)
      return [rets, []]
    else:
      assert isinstance(proof, LetProof)
      res = []
      call = algprob.resolveCall(values, calls[0])
      self.unifyCalls(proof.call, call)
      for retTuple, restProof in proof.proofDict.items():
        expandRest = expandProofHelper(self, values + [retTuple], calls[1:], rets, restProof)
        for retValues, factors in expandRest:
          res.append((retValues, [ProbLabel(call, retTuple)] + factors))
      return res


  def expandProof(self, call, proof):
    call = self.resolveCall(call)
    distrResult = self.model.getDistribution(call)
    distr = distrResult.distribution
    exp = expandProofHelper(self, [], distr.calls, distr.result, proof)
    for vals,factors in exp:
      label = ProbLabel(call, vals)
      self.labelPolys[label].append(factors)

  def expandProofSystem(self, proofSystem):
    self.labelPolys = defaultdict(lambda: [])

    varUses = defaultdict(lambda: 0)
    for call in proofSystem:
      for param in call.parameters:
        if isinstance(param, Variable):
          varUses[param] += 1

    for call,proof in proofSystem.items():
      self.expandProof(call, proof)
      for var,ref in self.popNewVars():
        self.model.modifyReferenceCount(ref, varUses[ref] - 1)

  def createNumericPolys(self):
    self.labels = list(self.labelPolys)
    self.invLabels = {}
    for i,label in self.labels:
      self.invLabels[label] = i
    self.numLabelPolys = {}
    for i,label in enumerate(labels):
      numTerms = []
      for factors in self.labelPolys[label]:
        logCoeff = 0
        numFactors = []
        for factor in factors:
          if factor.call.function == 'bernouli':
            (probVal,) = factor.call.parameters
            probRef = self.resolveValue(probVal)
            prob = self.model.JSONToRef(probRef)
            assert 0 <= prob <= 1
            (resVal,) = factor.result
            resRef = self.resolveValue(resVal)
            res = self.model.JSONToRef(resRef)
            assert res in [True, False]
            if res:
              probCorrect = prob
            else:
              probCorrect = 1 - prob
            logCoeff += math.log(probCorrect)
          else:
            assert factor in self.invLabels
            numFactors.append(self.invLabels[factor])
        numTerms.append((logCoeff, numFactors))
      self.numLabelPolys[i] = numTerms


  def sortCalls(self):
    graph = {}
    for i,terms in self.numLabelPolys.items():
      refs = set([])
      for factors in terms:
        for factor in factors:
          refs.add(factor)
      graph[i] = list(refs)
    components = graphsort.robust_topological_sort(graph)
    components.reverse()
    return components

  def updateProb(self, i):
    def termProb(term):
      return term[0] + sum(self.logProbs[j] for j in term[1])
    oldLogProb = self.logProbs[i]
    self.logProbs[i] = util.sumByLogs(map(termProb, self.numLabelPolys[i]))
    return self.logProbs[i] - oldLogProb


  def solveSCC(self, component):
    while True:
      change = 0
      for i in component:
        change += self.updateProb(i)
      if change <= 0.00001:
        break

  def solveSystem(self):
    for component in self.sortCalls():
      self.solveSCC(component)

  def solveProofSystem(self, proofSystem):
    self.expandProofSystem(proofSystem)
    self.createNumericPolys()
    self.solveSystem()

  def getFinalResult(self):
    res = {}
    for i,logProb in self.logProbs.items():
      res[self.labels[i]] = logProb
    return res



def evaluateProof(model, proofSystem, timePenaltyRate):
  sys = ProofSystem(model, timePenaltyRate)
  sys.solveProofSystem(proofSystem)
  return sys.getFinalResult()



















