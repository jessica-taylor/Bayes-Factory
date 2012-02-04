# Some classes for representing distributions (the things returned by getDistribution).

import random

from util import makeDataClass


# class Literal(object):
#   pass

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
    from proof import Variable
    typ = jsonObj['type']
    if typ == 'literal':
      return LiteralRef(jsonObj['ref'])
    if typ == 'callRef':
      return CallRef(jsonObj['callIndex'], jsonObj['valueIndex'])
    if typ == 'variable':
      return Variable(jsonObj['varid'])
    raise Exception("bad DistrValue type in JSON: " + typ)


class LiteralRef(DistrValue):
  """
  A LiteralRef is a reference to an object in the model.  It has an integer
  ref field, which identifies which object it points to.
  """

  def __init__(self, ref):
    assert isinstance(ref, int)
    self.ref = ref

  def __str__(self):
    return '@%s' % self.ref

  def getData(self):
    return self.ref

  def toJSON(self):
    return {'type': 'literal', 'ref': self.ref}

  @staticmethod
  def fromJSON(jsonObj):
    res = DistrValue.fromJSON(jsonObj)
    assert isinstance(res, LiteralRef)
    return res

makeDataClass(LiteralRef)


class CallRef(DistrValue):
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

  def __str__(self):
    return '$(' + str(self.callIndex) + ', ' + str(self.valueIndex) + ')'

  def getData(self):
    return (self.callIndex, self.valueIndex)

  def toJSON(self):
    return {'type': 'callRef', 'callIndex': self.callIndex, 'valueIndex': self.valueIndex}

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

  def __str__(self):
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



class Distribution(object):
  """
  What a model returns given a distribution call.  It's a Bayesian graph
  connecting distribution functions and values together.  It is specified as
  a list of calls (whose CallRefs can refer to earlier calls) and a list of
  return values (whose CallRefs can refer to any call).
  """

  def __init__(self, calls, result):
    assert Distribution.isLegalDistributionData(calls, result)
    self.calls = calls
    self.result = result

  @staticmethod
  def isLegalDistributionData(calls, result):
    """
    Checks if (calls, result) are valid arguments to the constructor.
    """
    def isValueLegal(i, value):
      assert isinstance(value, DistrValue)
      if isinstance(value, CallRef):
        return 0 <= value.callIndex < i
      else:
        return True

    def isCallLegal(i, call):
      return all(isValueLegal(i, value) for value in call.parameters)

    return all(isCallLegal(i, call) for i,call in enumerate(calls)) \
       and all(isValueLegal(len(calls), r) for r in result)

  def __str__(self):
    return '\n'.join(list(map(str, self.calls)) + [' '.join(map(str, self.result))])

  def getData(self):
    return (self.calls, self.result)

  def toJSON(self):
    return {'calls': [c.toJSON() for c in self.calls],
            'result': [r.toJSON() for r in self.result]}

  @staticmethod
  def fromJSON(jsonObj):
    return DistrCall(
      [DistrCall.fromJSON(c) for c in jsonObj['calls']],
      [DistrValue.fromJSON(r) for r in jsonObj['result']]
    )

makeDataClass(Distribution)
