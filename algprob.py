from collections import defaultdict
import numbers
import random

from distribution import CallRef, DistrCall, Distribution, LiteralRef,
from model import DistributionResult, Model



def resolveValue(values, val):
  if isInstance(val, CallRef):
    return values[val.callIndex][val.valueIndex]
  return val

def resolveCall(values, call):
  return DistrCall(call.family, tuple(resolveValue(values, v) for v in call.parameters))

def distributionLiteralRefs(distr):
  res = []
  def process(value):
    if isinstance(value, LiteralRef):
      res.append(value)
  for call in distr.calls:
    for param in call.parameters:
      process(param)
  for result in distr.result:
    process(result)
  return res



def sampleDistr(model, distribution):
  assert isinstance(model, Model)
  assert isinstance(distribution, Distribution)
  values = []
  for call in distribution.calls:
    values.append(sample(model, resolveCall(values, call)))
  return tuple(resolveValue(values, r) for r in distribution.result)


def sample(model, call):
  assert isinstance(model, Model)
  assert isinstance(call, DistrCall)
  if call.family == 'bernouli':
    assert len(call.parameters) == 1
    p = model.writeJSON(call.parameters[0])
    assert isinstance(p, numbers.Real)
    assert 0 <= p <= 1
    model.modifyReferenceCount(call.parameters[0], -1)
    res = random.random() < p
    return [model.readJSON(res)]
  distrResult = model.getDistribution(call)
  return sampleDistr(model, distrResult.distribution)



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
    return DistrCall(call.family, map(self.resolveValue, call.parameters))

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
    assert proofCall.family == distrCall.family
    assert len(proofCall.parameters) == len(distrCall.parameters)
    for p,d in zip(proofCall.parameters, distrCall.parameters):
      self.unify(p, d)

  def popNewVars(self):
    newVars = self.newVars
    self.newVars = []
    return newVars

  def expandProofHelper(self, values, calls, rets, proof):
    resolve = lambda x: resolveValue(values, x)
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
      call = resolveCall(values, calls[0])
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



class TestModel(Model):

  def getDistribution(self, family, parameters):
    if family == 'biasFromBool':
      assert len(parameters) == 1
      res = 50
      if parameters[0].getIntValue():
        res = 80
      return Distribution([], [intToBytes(res)])

    if family == 'decideBias':
      assert len(parameters) == 0
      return Distribution([
        DistrCall('bernouli', [intToBytes(1), intToBytes(2)], ['#']),
        DistrCall('biasFromBool', [CallRef(ValueType.BYTES, 0, 0)], ['#'])
      ], [CallRef(ValueType.BYTES, 1, 0)])

    #if family == 'flipCoin':
    #  assert len(pa

def test():
  model = TestModel()
  print model.getDistribution('decideBias', [])
  for i in range(20):
    res = sample(model, 'decideBias', [])
    print ' '.join(map(str, res))

test()



