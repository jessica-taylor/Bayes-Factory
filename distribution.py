# Some classes for representing distributions (the things returned by getDistribution).

import random

from util import makeDataClass, prettyString



class DistrValue(object):
  """
  Superclass for things that can be passed to or returned from a distribution function.
  """

  @staticmethod
  def fromJSON(jsonObj):
    """
    Converts JSON representing any DistrValue (including subclasses) back into
    a DistrValue.
    """
    from proof import ProofVar
    typ = jsonObj['type']
    if typ == 'literal':
      return LiteralRef(jsonObj['ref'])
    if typ == 'local':
      return LocalVariable(jsonObj['name'])
    if typ == 'proofvar':
      return ProofVar(jsonObj['varid'])
    raise Exception("bad DistrValue type in JSON: " + typ)


class LiteralRef(DistrValue):
  """
  A LiteralRef is a reference to an object in the model.  It has an integer
  ref field, which identifies which object it points to.
  """

  def __init__(self, ref):
    assert isinstance(ref, int)
    self.ref = ref

  def prettyString(self):
    return '@%s' % self.ref

  def getData(self):
    return (self.ref,)

  def toJSON(self):
    return {'type': 'literal', 'ref': self.ref}

  @staticmethod
  def fromJSON(jsonObj):
    res = DistrValue.fromJSON(jsonObj)
    assert isinstance(res, LiteralRef)
    return res

makeDataClass(LiteralRef)

class LocalVariable(DistrValue):
  """
  A reference to a variable assigned from some call.
  """

  def __init__(self, name):
    assert isinstance(name, str)
    self.name = name

  def prettyString(self):
    return '$%s' % self.name

  def getData(self):
    return (self.name,)

  def toJSON(self):
    return {'type': 'local', 'name': self.name}

  @staticmethod
  def fromJSON(jsonObj):
    res = DistrValue.fromJSON(jsonObj)
    assert isinstance(res, LocalVariable)
    return res

makeDataClass(LocalVariable)


class CallRef(object):
  """
  Represents a reference to a value returned by a call to an earlier
  distribution.  Contains a callIndex (which call the value was returned by)
  and valueIndex (which return value of that call this is).
  """

  def __init__(self, callIndex, valueIndex):
    assert isinstance(callIndex, int)
    assert isinstance(valueIndex, int)
    self.callIndex = callIndex
    self.valueIndex = valueIndex

  def prettyString(self):
    return '$(' + str(self.callIndex) + ', ' + str(self.valueIndex) + ')'

  def getData(self):
    return (self.callIndex, self.valueIndex)

  def toJSON(self):
    return {'callIndex': self.callIndex, 'valueIndex': self.valueIndex}

makeDataClass(CallRef)



class DistrCall(object):
  """
  A DistrCall (distribution call) consists of a distribution function
  (identified by a string) and parameters to pass to the function (represented
  by DistrValues).
  """

  def __init__(self, function, parameters):
    assert isinstance(function, str)
    parameters = tuple(parameters)
    assert all(isinstance(p, DistrValue) for p in parameters)
    self.function = function
    self.parameters = parameters

  def prettyString(self):
    return ' '.join(map(str, [self.function] + list(self.parameters)))

  def getData(self):
    return (self.function, self.parameters)

  def toJSON(self):
    return {'function': self.function,
            'parameters': [p.toJSON() for p in self.parameters]}

  def isPrimitive(self):
    return self.function == 'bernouli'

  @staticmethod
  def fromJSON(jsonObj):
    return DistrCall(
      jsonObj['function'],
      [DistrValue.fromJSON(p) for p in jsonObj['parameters']]
    )


makeDataClass(DistrCall)

class DistrCallAssignment(object):

  def __init__(self, call, variables):
    assert isinstance(call, DistrCall)
    variables = tuple(variables)
    assert all(isinstance(v, str) for v in variables)
    self.call = call
    self.variables = variables

  def getData(self):
    return (self.call, self.variables)

  def prettyString(self):
    return ' '.join(self.variables) + ' ' + self.call.prettyString()

  def toJSON(self):
    return {'call': self.call.toJSON(),
            'variables': list(self.variables)}

  @staticmethod
  def fromJSON(jsonObj):
    return DistrCallAssignment(
      DistrCall.fromJSON(jsonObj['call']),
      jsonObj['variables']
    )

makeDataClass(DistrCallAssignment)

class Distribution(object):
  """
  What a model returns given a distribution call.  It's a Bayesian graph
  connecting distribution functions and values together.  It is specified as
  a list of calls (whose CallRefs can refer to earlier calls) and a list of
  return values (whose CallRefs can refer to any call).
  """

  def __init__(self, assignments, result):
    Distribution.assertLegalDistributionData(assignments, result)
    self.assignments = assignments
    self.result = result

  @staticmethod
  def assertLegalDistributionData(assignments, result):
    """
    Checks if (calls, result) are valid arguments to the constructor.
    """
    variables = set([])
    def assertValueLegal(value):
      assert isinstance(value, DistrValue)
      if isinstance(value, LocalVariable):
        assert value.name in variables

    def assertCallLegal(call):
      for value in call.parameters:
        assertValueLegal(value)

    def assertAssignmentLegal(assn):
      assertCallLegal(assn.call)
      for v in assn.variables:
        assert v not in variables
        variables.add(v)

    for assn in assignments:
      assertAssignmentLegal(assn)
    for r in result:
      assertValueLegal(r)

  def prettyString(self):
    return '\n'.join(list(map(prettyString, self.assignments)) + \
                          [' '.join(map(prettyString, self.result))])

  def getData(self):
    return (self.assignments, self.result)

  def toJSON(self):
    return {'assignments': [a.toJSON() for a in self.assignments],
            'result': [r.toJSON() for r in self.result]}

  @staticmethod
  def fromJSON(jsonObj):
    return DistrCall(
      [DistrCall.fromJSON(a) for a in jsonObj['assignments']],
      [DistrValue.fromJSON(r) for r in jsonObj['result']]
    )

makeDataClass(Distribution)
