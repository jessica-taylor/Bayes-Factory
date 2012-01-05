import numbers
import random

def makeDataClass(cls):

  def clsCmp(self, other):
    return cmp(self.getData(), other.getData())

  def clsHash(self):
    return hash(cls) ^ hash(self.getData())

  cls.__cmp = clsCmp
  cls.__hash__ = clsHash

class Literal(object):
  pass

class LiteralString(Literal):

  def __init__(self, string):
    assert isinstance(string, basestring)
    self.string = string

  def __str__(self):
    return repr(self.string)

  def getData(self):
    return self.string

makeDataClass(LiteralString)

class LiteralRef(Literal):

  def __init__(self, ref):
    assert isinstance(ref, numbers.Integral)
    self.ref = ref

  def __str__(self):
    return '@' + self.ref

  def getData(self):
    return self.ref

makeDataClass(LiteralRef)


class Variable(object):

  def __init__(self, callIndex, valueIndex):
    assert isinstance(callIndex, numbers.Integral)
    assert isinstance(valueIndex, numbers.Integral)
    self.callIndex = callIndex
    self.valueIndex = valueIndex

  def __str__(self):
    return '$(' + str(self.callIndex) + ', ' + str(self.valueIndex) + ')'

  def getData(self):
    return (self.callIndex, self.valueIndex)

makeDataClass(Variable)

def isDistrValue(x):
  return isinstance(x, Literal) or isinstance(x, Variable)

class DistrCall(object):

  def __init__(self, constructor, params):
    assert isinstance(constructor, basestring)
    params = tuple(params)
    # assert all(map(isDistrValue, params))
    self.constructor = constructor
    self.params = params

  def __str__(self):
    return ' '.join(map(str, [self.constructor] + self.params))

  def getData(self):
    return (self.constructor, self.params)

makeDataClass(DistrCall)

# def isLegalDistributionData(calls, result):
#   def isValueLegal(i, value):
#     if isinstance(value, LiteralDistrValue):
#       return True
#     assert isinstance(value, Variable)
#     if not 0 <= value.callIndex < i:
#       return False
#     call = calls[value.callIndex]
#     if not 0 <= value.valueIndex < len(call.retTypes):
#       return False
#     return value.vtype == call.retTypes[value.valueIndex]
#   def isCallLegal(i, call):
#     return all(isValueLegal(i, value) for value in call.params)
#   return all(isCallLegal(i, call) for i,call in enumerate(calls)) \
#       and all(isValueLegal(len(calls), r) for r in result)


class Distribution(object):

  def __init__(self, calls, result):
    # assert isLegalDistributionData(calls, result)
    self.calls = calls
    self.result = result

  def __str__(self):
    return '\n'.join(map(str, self.calls)) + '\n' + ' '.join(map(str, self.result))

  def getData(self):
    return (self.calls, self.result)

makeDataClass(Distribution)

class Model(object):

  def getDistribution(self, constructor, params):
    raise Exception("not implemented")

  def serialize(self, ref):
    raise Exception("not implemented")

  def unserialize(self, byts):
    raise Exception("not implemented")

  def modifyReferenceCount(self, ref, delta):
    raise Exception("not implemented")

  def readString(self, string):
    raise Exception("not implemented")

  def writeString(self, ref):
    raise Exception("not implemented")

  def isEqual(self, aref, bref):
    return False

def resolveValue(values, val):
  if isInstance(val, Variable):
    return values[val.callIndex][val.valueIndex]
  return val

def resolveCall(values, call):
  return DistrCall(call.constructor, tuple(resolveValue(values, v) for v in call.params))

def distributionLiteralRefs(distr):
  res = []
  def process(value):
    if isinstance(value, LiteralRef):
      res.append(value)
  for call in distr.calls:
    for param in call.params:
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


def sample(model, constructor, params):
  assert isinstance(model, Model)
  assert isinstance(constructor, basestring)
  if constructor == 'bernouli':
    assert len(params) == 1
    p = float(model.writeString(params[0]))
    model.modifyReferenceCount(params[0], -1)
    assert 0 <= p <= 1
    res = random.random() < p
    return [LiteralString("1" if res else "0")]
  return sampleDistr(model, model.getDistribution(constructor, params))

class ProofVar(object):
  def __init__(self, varid):
    assert isinstance(varid, numbers.Integral)
    self.varid = varid

  def getData(self):
    return self.varid

makeDataClass(ProofVar)

class ProbLabel(object):

  def __init__(self, call, result):
    assert isinstance(call, DistrCall)
    result = tuple(result)
    assert all(isinstance(x, Literal) for x in result)
    self.call = call
    self.result = result

  def getData(self):
    return (self.call, self.result)

makeDataClass(ProbLabel)



def isProofValue(x):
  return isinstance(x, Literal) or isinstance(x, ProofVar)

class Proof(object):
  def __init__(self):
    pass

class ReturnProof(Proof):
  def __init__(self, valueList):
    valueList = tuple(valueList)
    assert all(map(isProofValue, valueList))
    self.valueList = valueList

  def getData(self):
    return self.valueList

makeDataClass(ReturnProof)

class LetProof(Proof):
  def __init__(self, call, proofDict):
    assert isinstance(call, DistrCall)
    self.call = call
    self.proofDict = {}
    for values,restProof in proofDict.values():
      values = tuple(values)
      assert all(map(isProofValue, values))
      assert isinstance(restProof, Proof)
      self.proofDict[values] = restProof

makeDataClass(LetProof)


class ProofEnv(object):

  def __init__(self, model):
    self.model = model
    self.varValues = {}
    self.newVars = []
    self.labelPolys = {}

  def resolveValue(value):
    if isinstance(value, ProofVar):
      assert value.varid in self.varValues
      return self.varValues[value.varid]
    return value

  def resolveCall(call):
    assert isinstance(call, DistrCall)
    return DistrCall(call.constructor, map(self.resolveValue, call.params))

  def unify(self, proofValue, retValue):
    assert isinstance(retValue, Literal)
    if isinstance(proofValue, ProofVar):
      varid = proofValue.varid
      if varid in self.varValues:
        varValue = self.varValues[varid]
        assert self.model.isEqual(varValue, retValue)
        self.model.modifyReferenceCount(retValue, -1)
      else:
        self.varValues[varid] = retValue
        self.newVars.append((proofValue, retValue))
    else:
      assert isinstance(proofValue, Literal)
      assert self.model.isEqual(proofValue, retValue)

  def unifyCalls(self, proofCall, distrCall):
    assert proofCall.constructor == distrCall.constructor
    assert len(proofCall.params) == len(distrCall.params)
    for p,d in zip(proofCall.params, distrCall.params):
      self.unify(p, d)

  def popNewVars(self):
    newVars = self.newVars
    self.newVars = []
    return newVars

  def expandProofHelper(self, values, calls, rets, proof):
    resolve = lambda x: resolveValue(values, x)
    if len(calls) == 0:
      assert isinstance(proof, ReturnProof)
      assert len(proof.valueList) == len(rets)
      rets = [resolveValue(values, r) for r in rets]
      for p,r in zip(proof.valueList, rets):
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
    distr = self.model.getDistribution(call)
    exp = expandProofHelper(self, [], distr.calls, distr.result, proof)
    for vals,factors in exp:
      label = ProbLabel(call, vals)
      if label not in self.labelPolys:
        self.labelPolys[label] = []
      self.labelPolys[label].append(factors)

  def expandProofSystem(self, proofSystem):
    varUses = {}
    for call in proofSystem:
      for param in call.params:
        if isinstance(param, ProofVar):
          if param not in varUses:
            varUses[param] = 0
          varUses[param] += 1

    for call,proof in proofSystem.items():
      self.expandProof(call, proof)
      for var,ref in self.popNewVars():
        numUses = 0
        if ref in varUses:
          numUses = varUses[ref]
        self.model.modifyReferenceCount(ref, numUses - 1)



class TestModel(Model):

  def getDistribution(self, constructor, params):
    if constructor == 'biasFromBool':
      assert len(params) == 1
      res = 50
      if params[0].getIntValue():
        res = 80
      return Distribution([], [intToBytes(res)])

    if constructor == 'decideBias':
      assert len(params) == 0
      return Distribution([
        DistrCall('bernouli', [intToBytes(1), intToBytes(2)], ['#']),
        DistrCall('biasFromBool', [Variable(ValueType.BYTES, 0, 0)], ['#'])
      ], [Variable(ValueType.BYTES, 1, 0)])

    #if constructor == 'flipCoin':
    #  assert len(pa

def test():
  model = TestModel()
  print model.getDistribution('decideBias', [])
  for i in range(20):
    res = sample(model, 'decideBias', [])
    print ' '.join(map(str, res))

test()



