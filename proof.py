from distribution import DistrCall, DistrValue, LiteralRef
from util import makeDataClass

class Variable(DistrValue):
  def __init__(self, varid):
    assert isinstance(varid, int)
    self.varid = varid

  def getData(self):
    return self.varid

  def toJSON(self):
    return {'type': 'variable', 'varid': self.varid}

makeDataClass(Variable)

class ProbLabel(object):

  def __init__(self, call, result):
    assert isinstance(call, DistrCall)
    result = tuple(result)
    assert all(isinstance(x, LiteralRef) for x in result)
    self.call = call
    self.result = result

  def getData(self):
    return (self.call, self.result)

  def toJSON(self):
    return {'call': self.call.toJSON(),
            'result': [r.toJSON() for r in self.result]}

makeDataClass(ProbLabel)



def isProofValue(x):
  return isinstance(x, Literal) or isinstance(x, Variable)

class Proof(object):
  def __init__(self):
    pass

class ResultProof(Proof):
  def __init__(self, result):
    result = tuple(result)
    assert all(map(isProofValue, result))
    self.result = result

  def getData(self):
    return self.result

  def toJSON(self):
    return {'type': 'result',
            'result': [r.toJSON() for r in self.result]}

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

  def getData(self):
    return (self.call, self.proofDict)

  def toJSON(self):
    return {'type': 'let',
            'call': call.toJSON(),
            'proofDict': [
              {'values': [v.toJSON() for v in values],
               'restProof': restProof.toJSON()}
              for values,restProof in self.proofDict.items()
            ]}


makeDataClass(LetProof)
