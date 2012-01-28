# Data classes related to proof systems for models.

from distribution import DistrCall, DistrValue, LiteralRef
from util import makeDataClass

class Variable(DistrValue):
  """
  A placeholder for use in a DistrCall or Distribution.  Multiple uses of the
  same variable should be equal.
  """
  def __init__(self, varid):
    assert isinstance(varid, int)
    self.varid = varid

  def getData(self):
    return self.varid

  def toJSON(self):
    return {'type': 'variable', 'varid': self.varid}

makeDataClass(Variable)

def isProofValue(value):
  return isinstance(value, LiteralRef) or isinstance(value, Variable)

class ProbLabel(object):
  """
  Collection of a DistrCall and its results (as LiteralRefs).  This can be
  assigned a probability, the probability that the call produces objects
  equal to the results.
  """

  def __init__(self, call, result):
    assert isinstance(call, DistrCall)
    assert all(map(isProofValue, call.parameters))
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




class Proof(object):
  """
  A proof proves a lower bound on the probability of a ProbLabel in terms of other
  ProbLabels.  It is a recursive structure of LetProofs, eventually coming to a
  ReturnProof.  The depth of nesting should be equal to the number of calls in the
  ProbLabel's DistrCall's Distribution.
  """
  def __init__(self):
    pass

class ResultProof(Proof):
  """
  Should be at level (number of calls in the Distribution).  States the results of the
  Distribution as a tuple.
  """
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
  """
  Should be at intermediate levels.  States the current DistrCall and a dictionary
  mapping possible return values of the DistrCall to proofs on the condition that the
  DistrCall returns that value.
  """
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
