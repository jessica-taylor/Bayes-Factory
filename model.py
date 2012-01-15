import distribution
from distribution import LiteralRef, Distribution
from util import makeDataClass

class DistributionResult:

  def __init__(self, distribution, time):
    assert isinstance(distribution, Distribution)
    self.distribution = distribution
    self.time = float(time)

  def getData(self):
    return (self.distribution, self.time)

  def toJSON(self):
    return {'distribution': self.distribution.toJSON(),
            'time': self.time}

  @staticmethod
  def fromJSON(jsonObj):
    return DistributionResult(
      Distribution.fromJSON(jsonObj['distribution']),
      jsonObj['time']
    )

makeDataClass(DistributionResult)


class Model(object):

  def getDistribution(self, call):
    raise Exception("not implemented")

  # def serialize(self, ref):
  #   raise Exception("not implemented")

  # def unserialize(self, byts):
  #   raise Exception("not implemented")

  def modifyReferenceCount(self, ref, delta):
    raise Exception("not implemented")

  def readJSON(self, jsonObj):
    raise Exception("not implemented")

  def writeJSON(self, ref):
    raise Exception("not implemented")

  def isEqual(self, aref, bref):
    return False

class WrappedModel(Model):

  def __init__(self, wrapped):
    self.wrapped = wrapped

  def getDistribution(self, call):
    assert isinstance(call, DistrCall)
    assert all(isInstance(p, LiteralRef) for p in call.parameters)
    result = self.wrapped.getDistribution(call)
    assert isinstance(result, DistributionResult)
    return result

  def modifyReferenceCount(self, ref, delta):
    assert isinstance(ref, LiteralRef)
    assert isinstance(delta, int)
    if delta != 0:
      self.wrapped.modifyReferenceCount(ref, delta)

  def readJSON(self, jsonObj):
    result = self.wrapped.readJSON(jsonObj)
    assert isinstance(result, LiteralRef)
    return result

  def writeJSON(self, ref):
    assert isinstance(ref, LiteralRef)
    result = self.wrapped.writeJSON(ref)
    return result

  def isEqual(self, aref, bref):
    assert isinstance(aref, LiteralRef)
    assert isinstance(bref, LiteralRef)
    if aref == bref:
      return True
    return self.wrapped.isEqual(aref, bref)






