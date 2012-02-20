# Data classes related to proof systems for models.

import algprob
from distribution import DistrCall, DistrValue, Distribution, LiteralRef
from util import makeDataClass

class ProofVar(DistrValue):
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
    return {'type': 'proofvar', 'varid': self.varid}

makeDataClass(ProofVar)

def isProofValue(value):
  return isinstance(value, LiteralRef) or isinstance(value, ProofVar)

class ProbLabel:
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

class VariableMapping:
  """
  Mapping of variable name to value (LiteralRef or ProofVar).
  """

  def __init__(self, values):
    if isinstance(values, dict):
      values = values.items()
    self.values = {}
    for k,v in values:
      assert isinstance(k, str)
      assert isinstance(v, LiteralRef) or isinstance(v, ProofVar)
      self.values[k] = v

  def getData(self):
    return (sorted(tuple(self.values.items())),)

  def getCallLabels(self, distr):
    assert isinstance(distr, Distribution)
    values = {}
    labels = []
    for assn in distr.assignments:
      call = algprob.resolveCall(values, assn.call)
      result = [self.values[v] for v in assn.variables]
      algprob.addValues(values, assn.variables, result)
      labels.append(ProbLabel(call, result))
    return labels


makeDataClass(VariableMapping)

class Proof:

  def __init__(self, label, mappings):
    assert isinstance(label, ProbLabel)
    mappings = tuple(mappings)
    assert all(isinstance(x, VariableMapping) for x in mappings)
    if len(mappings) > 0:
      keys = mappings[0].values.keys()
      assert all(x.values.keys() == keys for x in mappings)
    self.label = label
    self.mappings = mappings

  def getData(self):
    return (self.label, self.mappings)

  def getCallLabelsList(self, distr):
    assert isinstance(distr, Distribution)
    return [m.getCallLabels(distr) for m in self.mappings]

  # def prettyString(self):
  #   def callLabelsStr(callLabels):
  #     return '{' + '; '.join(map(str, callLabels)) + '}'
  #   return str(self.label) + " : " + ', '.join(map(callLabelsStr, self.callLabelsList))


makeDataClass(Proof)

