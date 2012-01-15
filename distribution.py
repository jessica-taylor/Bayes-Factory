
import util
import random


# class Literal(object):
#   pass

# class LiteralString(Literal):
#
#   def __init__(self, string):
#     assert isinstance(string, basestring)
#     self.string = string
#
#   def __str__(self):
#     return repr(self.string)
#
#   def getData(self):
#     return self.string
#
# makeDataClass(LiteralString)

class DistrValue(object):

  @staticmethod
  def fromJSON(jsonObj):
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

  def __init__(self, ref):
    assert isinstance(ref, int)
    self.ref = ref

  def __str__(self):
    return '@' + self.ref

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

def isDistrValue(x):
  return isinstance(x, LiteralRef) or isinstance(x, CallRef)

class DistrCall(object):

  def __init__(self, family, parameters):
    assert isinstance(family, str)
    parameters = tuple(parameters)
    # assert all(map(isDistrValue, parameters))
    self.family = family
    self.parameters = parameters

  def __str__(self):
    return ' '.join(map(str, [self.family] + self.parameters))

  def getData(self):
    return (self.family, self.parameters)

  def toJSON(self):
    return {'family': self.family,
            'parameters': [p.toJSON() for p in self.parameters]}

  @staticmethod
  def fromJSON(jsonObj):
    return DistrCall(
      jsonObj['family'],
      [DistrValue.fromJSON(p) for p in jsonObj['parameters']]
    )


makeDataClass(DistrCall)

# def isLegalDistributionData(calls, result):
#   def isValueLegal(i, value):
#     if isinstance(value, LiteralDistrValue):
#       return True
#     assert isinstance(value, CallRef)
#     if not 0 <= value.callIndex < i:
#       return False
#     call = calls[value.callIndex]
#     if not 0 <= value.valueIndex < len(call.retTypes):
#       return False
#     return value.vtype == call.retTypes[value.valueIndex]
#   def isCallLegal(i, call):
#     return all(isValueLegal(i, value) for value in call.parameters)
#   return all(isCallLegal(i, call) for i,call in enumerate(calls)) \
#       and all(isValueLegal(len(calls), r) for r in result)


class Distribution(object):

  def __init__(self, calls, result):
    # assert isLegalDistributionData(calls, result)
    self.calls = calls
    self.result = result

  def __str__(self):
    return '\n'.join(map(str, self.calls) + [' '.join(map(str, self.result))])

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
