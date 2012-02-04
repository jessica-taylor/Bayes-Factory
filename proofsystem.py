
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


  def sortCalls(self):
    graph = {}
    for label,terms in self.labelPolys.items():
      refs = set([])
      for factors in terms:
        for factor in factors:
          if not factor.call.isPrimitive():
            refs.add(factor)
      graph[label] = list(refs)
    components = graphsort.robust_topological_sort(graph)
    components.reverse()
    return components

  def cachedProbability(self, label):
    if label.call.function == 'bernouli':
      (probVal,) = label.call.parameters
      probRef = self.resolveValue(probVal)
      prob = self.model.refToJSON(probRef)
      assert 0 <= prob <= 1
      (resVal,) = label.result
      resRef = self.resolveValue(resVal)
      res = self.model.refToJSON(resRef)
      assert res in [True, False]
      if res:
        return prob
      else:
        return 1 - prob
    else:
      return self.logProbs[label]


  def updateProb(self, label):
    def termProb(term):
      return sum(map(self.cachedProbability, term))
    oldLogProb = self.logProbs[label]
    self.logProbs[label] = util.sumByLogs(list(map(termProb, self.labelPolys[label])))
    if self.logProbs[label] == util.negInfinity:
      return 0.0
    return self.logProbs[label] - oldLogProb


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
    self.solveSystem()

  def getFinalResult(self):
    return dict(self.logProbs)


def evaluateProof(model, proofSystem, timePenaltyRate):
  env = ProofEnv(model, timePenaltyRate)
  env.solveProofSystem(proofSystem)
  return env.getFinalResult()


