import distribution
from distribution import LiteralRef, DistrCall, Distribution
from util import makeDataClass

class DistrResult:
  """
  The result of getDistribution.  Mainly contains a Distribution object, but
  can also contain time taken during the call.
  """

  def __init__(self, distribution, time=0.0):
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
    return DistrResult(
      Distribution.fromJSON(jsonObj['distribution']),
      jsonObj['time']
    )

makeDataClass(DistrResult)


class Model(object):
  """
  Represents a model (essentially a collection of random functions, along with
  the state of objects).  Each object in the model has a LiteralRef associated
  with it.  It also has a reference count.  When an object's reference count
  goes to 0 or below, it is considered dead and the model can delete it.
  """

  def getDistribution(self, call):
    """
    Given a call, returns a Distribution representing the result of the
    DistrCall.  Should be deterministic.  Any LiteralRefs in the parameters have
    their reference counts decremented by 1 per occurrence.  Any LiteralRefs in
    the resulting distributions should have their reference counts incremented
    by the number of occurrences.
    """
    raise Exception("not implemented")

  def modifyReferenceCount(self, ref, delta):
    """
    Increments the reference count of the LiteralRef by delta.  If delta is
    negative, the reference count will be reduced by -delta.
    """
    raise Exception("not implemented")

  def JSONToRef(self, jsonObj):
    """
    Given a JSON object (the result of json.loads), puts it in the system and
    initializes it with a reference count of 1.  A literalRef pointing to the
    object should be returned.
    """
    raise Exception("not implemented")

  def refToJSON(self, ref):
    """
    Given a LiteralRef, returns a JSON representation of the object.  Does not
    modify any reference counts.
    """
    raise Exception("not implemented")

  def isEqual(self, aref, bref):
    """
    Returns True iff. the object pointed to by aref is equal to the object
    pointed to by bref.  Should be equivalent to:
    refToJSON(aref) == refToJSON(bref)
    """
    raise Exception("not implemented")

class WrappedModel(Model):
  """
  An easier to use, safer, and more efficient wrapper around a model.
  Mostly behaves exactly the same as the original.
  """

  def __init__(self, wrapped):
    self.wrapped = wrapped

  def getDistribution(self, call):
    assert isinstance(call, DistrCall)
    assert all(isinstance(p, LiteralRef) for p in call.parameters)
    result = self.wrapped.getDistribution(call)
    assert isinstance(result, DistrResult)
    return result

  def modifyReferenceCount(self, ref, delta):
    assert isinstance(ref, LiteralRef)
    assert isinstance(delta, int)
    if delta != 0:
      self.wrapped.modifyReferenceCount(ref, delta)

  def JSONToRef(self, jsonObj):
    result = self.wrapped.JSONToRef(jsonObj)
    assert isinstance(result, LiteralRef)
    return result

  def refToJSON(self, ref):
    assert isinstance(ref, LiteralRef)
    result = self.wrapped.refToJSON(ref)
    return result

  def isEqual(self, aref, bref):
    assert isinstance(aref, LiteralRef)
    assert isinstance(bref, LiteralRef)
    if aref == bref:
      return True
    return self.wrapped.isEqual(aref, bref)






