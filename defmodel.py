from distribution import DistrCall, Distribution, LiteralString, LiteralRef, CallRef
from model import Model

import pickle


class PythonDistributionSystem(object):

  def __init__(self):
    self.callStack = []
    self.functions = {}


  def distribution(self):

    def wrapper(towrap):
      name = towrap.__name__

      def distrFunction(*args):
        self.callStack.append([])
        res = towrap(*args)
        return self.callStack.pop(), res
      self.functions[name] = distrFunction

      def wrapped(*args):
        res = CallRef(len(self.callStack[-1]), 0)
        self.callStack[-1].append((name, args))
        return res
      wrapped.__name__ = name
      return wrapped

    return wrapper

class PythonFunctionModel(algprob.Model):

  def __init__(self, functions):
    self.functions = functions
    self.referenced = {}
    self.referenceCount = 0

  def newReference(self):
    res = self.referenceCount
    self.referenceCount += 1
    return LiteralRef(res)

  def distrValueToObject(self, value):
    assert isinstance(value, LiteralRef)
    ref = value.ref
    assert ref in self.referenced
    res = pickle.loads(self.referenced[ref][0])
    self.modifyReferenceCount(value, -1)

  def internObject(self, obj):
    ref = self.newReference()
    self.referenced[ref] = [obj, 1]
    return ref

  def readJSON(self, string):
    return self.internObject(string)

  def writeJSON(self, ref):
    assert isinstance(ref, LiteralRef)
    return self.referenced[ref][0]


  def objectToDistrValue(self, obj):
    if isinstance(obj, CallRef):
      return obj
    return self.internObject(obj)


  def getDistribution(self, call):
    calls,ret = self.functions[call.family](map(self.distrValueToObject, call.parameters))
    return Distribution(
      [Call(family, map(self.objectToDistrValue, parameters))
       for family,parameters in calls],
      [objectToDistrValue(ret)]
    )

  def modifyReferenceCount(self, ref, inc):
    assert isinstance(ref, LiteralRef)
    ref = ref.ref
    assert ref in self.referenced
    data = self.referenced[ref]
    newCount = data[1] + inc
    assert newCount >= 0
    if newCount == 0:
      del self.referenced[ref]
    else:
      data[1] = newCount






