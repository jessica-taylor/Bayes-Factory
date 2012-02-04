from distribution import DistrCall, Distribution, LiteralRef, CallRef
from model import DistrResult, Model

def export(onlyFun=None):
  def wrapper(f):
    f._defmodel_export = True
    return f
  if hasattr(onlyFun, '__call__'):
    return wrapper(onlyFun)
  return wrapper

def isExport(f):
  return hasattr(f, '_defmodel_export') and f._defmodel_export

class PythonDistributionSystem(object):
  """
  A system of distribution functions, represented as a Python class.

  The class should @export distribution functions.
  """

  def __init__(self):
    self.callStack = []
    self.functions = {}
    for name in dir(type(self)):
      # this is necessary because of weird closure semantics
      def loopBody(name, towrap):
        if isExport(towrap):
          if name != 'bernouli':
            def distrFunction(args):
              self.callStack.append([])
              args = list(args)
              assert args != [None]
              res = towrap(*args)
              return self.callStack.pop(), res
            self.functions[name] = distrFunction

          def wrapped(*args):
            res = CallRef(len(self.callStack[-1]), 0)
            self.callStack[-1].append((name, args))
            return res
          wrapped.__name__ = name
          setattr(self, name, wrapped)
      loopBody(name, getattr(self, name))


  def getModel(self):
    return PythonFunctionModel(self.functions)

  @export
  def bernouli(self, prob):
    raise Exception("can't call bernouli in PythonDistributionSystem")

class PythonFunctionModel(Model):
  """
  A model made of Python functions.

  Usually derived from a PythonDistributionSystem.
  """

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
    assert value.ref in self.referenced
    res = self.referenced[value.ref][0]
    #self.modifyReferenceCount(value, -1)
    return res

  def internObject(self, obj):
    ref = self.newReference()
    self.referenced[ref.ref] = [obj, 1]
    return ref

  def JSONToRef(self, obj):
    return self.internObject(obj)

  def refToJSON(self, ref):
    assert isinstance(ref, LiteralRef)
    return self.referenced[ref.ref][0]


  def objectToDistrValue(self, obj):
    if isinstance(obj, CallRef):
      return obj
    return self.internObject(obj)


  def getDistribution(self, call):
    calls,ret = self.functions[call.function](map(self.distrValueToObject, call.parameters))
    distr = Distribution(
      [DistrCall(function, map(self.objectToDistrValue, parameters))
       for function,parameters in calls],
      [self.objectToDistrValue(ret)]
    )
    return DistrResult(distr, 0.0)

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







