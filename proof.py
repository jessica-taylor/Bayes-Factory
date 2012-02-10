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
    return (self.varid,)

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

  def prettyString(self):
    return str(self.call) + " -> " + ' '.join(map(str, self.result))

  def toJSON(self):
    return {'call': self.call.toJSON(),
            'result': [r.toJSON() for r in self.result]}

makeDataClass(ProbLabel)


class Proof(object):

  def __init__(self, label, callLabelsList):
    assert isinstance(label, ProbLabel)
    callLabelsList = tuple(map(tuple, callLabelsList))
    assert all(all(isinstance(x, ProbLabel) for x in xs)
               for xs in callLabelsList)
    if len(callLabelsList) > 0:
      length = len(callLabelsList[0])
      assert all(len(x) == length for x in callLabelsList)
    self.label = label
    self.callLabelsList = callLabelsList

  def getData(self):
    return (self.label, self.callLabelsList)

  def prettyString(self):
    def callLabelsStr(callLabels):
      return '{' + '; '.join(map(str, callLabels)) + '}'
    return str(self.label) + " : " + ', '.join(map(callLabelsStr, self.callLabelsList))

makeDataClass(Proof)


"""
class Proof(object):
  A proof proves a lower bound on the probability of a ProbLabel in terms of other
  ProbLabels.
  def __init__(self, labels):
    self.labels = tuple(labels)
    assert all(isinstance(x, ProbLabel) for x in self.labels)

  def getData(self):
    return self.labels

makeDataClass(Proof)
"""

