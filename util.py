
import math

def makeDataClass(cls):
  """
  Makes cls into a data class.

  cls should define a nullary method, getData(), which returns all the data
  contained in the instance (in a structure such as a tuple).  makeDataCLass
  defines comparison and hashing in terms of this function.
  """


  def clsCmp(self, other):
    return cmp(self.getData(), other.getData())

  def clsHash(self):
    return hash(cls) ^ hash(self.getData())
  cls.__hash__ = clsHash

  def clsRepr(self):
    return cls.__name__ + "(" + ", ".join(map(repr, self.getData())) + ")"
  cls.__repr__ = clsRepr

  def clsLt(self, other):
    return self.getData() < other.getData()
  cls.__lt__ = clsLt

  def clsLe(self, other):
    return self.getData() <= other.getData()
  cls.__le__ = clsLe

  def clsEq(self, other):
    return self.getData() == other.getData()
  cls.__eq__ = clsEq

  def clsNe(self, other):
    return self.getData() != other.getData()
  cls.__ne__ = clsNe

  def clsGe(self, other):
    return self.getData() >= other.getData()
  cls.__ge__ = clsGe

  def clsGt(self, other):
    return self.getData() > other.getData()
  cls.__gt__ = clsGt

negInfinity = float("-inf")

def prettyString(value):
  if hasattr(value, 'prettyString'):
    return value.prettyString()
  if isinstance(value, list):
    return '[' + ', '.join(map(prettyString, value)) + ']'
  return str(value)

def sumByLogs(xs):
  """
  Computes math.log(sum(map(math.exp, xs))) while minimizing rounding error.
  """
  if len(xs) == 0:
    return 1
  maxLog = max(xs)
  adjSum = sum(math.exp(x - maxLog) for x in xs)
  if adjSum == 0:
    return negInfinity
  return math.log(adjSum) + maxLog

def agrestiCoullLower(z, x, n):
  n2 = n + z**2
  p = (x + z**2/2) / n2
  return p - z * sqrt(p * (1 - p) / n2)

