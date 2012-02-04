
from collections import defaultdict
import json
import math
import numbers

import graphsort

from distribution import CallRef, DistrCall, Distribution, LiteralRef
from model import DistrResult, Model
from proof import Variable, Proof

import algprob
import util

class ProofEnv(object):

  def __init__(self, model, timePenaltyRate):
    self.model = model
    self.timePenaltyRate = timePenaltyRate
    self.distributionCache = {}
    self.varValues = {}
    self.newVars = []
    self.labelPolys = defaultdict(lambda: [])

  def getDistribution(self, call):
    if call not in self.distributionCache:
      self.distributionCache[call] = self.model.getDistribution(call)
    return self.distributionCache[call]

  def resolveValue(self, value):
    if isinstance(value, Variable):
      assert value.varid in self.varValues
      return self.varValues[value.varid]
    return value

  def resolveCall(self, call):
    assert isinstance(call, DistrCall)
    return DistrCall(call.function, map(self.resolveValue, call.parameters))

  def unify(self, proofValue, retValue):
    assert isinstance(retValue, LiteralRef)
    if isinstance(proofValue, Variable):
      varid = proofValue.varid
      if varid in self.varValues:
        varValue = self.varValues[varid]
        assert self.model.isEqual(varValue, retValue)
        #self.model.modifyReferenceCount(retValue, -1)
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

  def verifyCallLabels(self, label, distr, callLabels):
    values = []
    assert len(callLabels) == len(distr.calls)
    for call,callLabel in zip(distr.calls, callLabels):
      call = algprob.resolveCall(values, call)
      self.unifyCalls(callLabel.call, call)
      values.append(callLabel.result)
    assert len(distr.result) == len(label.result)
    for distrRes,labelRes in zip(distr.result, label.result):
      distrRes = algprob.resolveValue(values, distrRes)
      self.unify(labelRes, distrRes)

  def isCallLabelsListDisjoint(self, callLabelsList, startIndex=0):
    if len(callLabelsList) <= 1:
      return True
    length = len(callLabelsList[0])
    if startIndex >= length:
      return False
    jsonMapping = defaultdict(lambda: [])
    for callLabels in callLabelsList:
      def valueToJSON(value):
        return self.model.refToJSON(self.resolveValue(value))
      json = [valueToJSON(v) for v in callLabels[startIndex].result]
      jsonStr = json.dumps(json)
      jsonMapping[jsonStr].append(callLabels)
    for callLabelsList in jsonMapping.values():
      if not self.isCallLabelsDisjoint(callLabelsList, startIndex + 1):
        return False
    return True


  def expandProof(self, proof):
    assert self.isCallLabelsListDisjoint(proof.callLabelsList)
    label = proof.label
    call = self.resolveCall(label.call)
    distrResult = self.getDistribution(call)
    distr = distrResult.distribution
    for callLabels in proof.callLabelsList:
      self.verifyCallLabels(label, distr, callLabels)
      self.labelPolys[label].append(callLabels)


  def expandProofSystem(self, proofSystem):
    for proof in proofSystem:
      self.expandProof(proof)

  def createNumericPolys(self):
    self.labels = list(self.labelPolys)
    self.invLabels = {}
    for i,label in enumerate(self.labels):
      self.invLabels[label] = i
    self.numLabelPolys = {}
    for i,label in enumerate(self.labels):
      numTerms = []
      for factors in self.labelPolys[label]:
        logCoeff = 0
        numFactors = []
        for factor in factors:
          if factor.call.function == 'bernouli':
            (probVal,) = factor.call.parameters
            probRef = self.resolveValue(probVal)
            prob = self.model.refToJSON(probRef)
            assert 0 <= prob <= 1
            (resVal,) = factor.result
            resRef = self.resolveValue(resVal)
            res = self.model.refToJSON(resRef)
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
      for _,factors in terms:
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
    self.logProbs[i] = util.sumByLogs(list(map(termProb, self.numLabelPolys[i])))
    if self.logProbs[i] == util.negInfinity:
      return 0.0
    return self.logProbs[i] - oldLogProb


  def solveSCC(self, component):
    while True:
      change = 0
      for i in component:
        change += self.updateProb(i)
      if change <= 0.00001:
        break

  def solveSystem(self):
    self.logProbs = defaultdict(lambda: util.negInfinity)
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
  env = ProofEnv(model, timePenaltyRate)
  env.solveProofSystem(proofSystem)
  return env.getFinalResult()


