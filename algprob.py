from collections import defaultdict
import math
import numbers
import random

import graphsort

from distribution import CallRef, DistrCall, Distribution, LiteralRef
from model import DistrResult, Model


def resolveValue(values, val):
  if isinstance(val, CallRef):
    return values[val.callIndex][val.valueIndex]
  return val

def resolveCall(values, call):
  return DistrCall(call.function, tuple(resolveValue(values, v) for v in call.parameters))

def distributionLiteralRefs(distr):
  res = []
  def process(value):
    if isinstance(value, LiteralRef):
      res.append(value)
  for call in distr.calls:
    for param in call.parameters:
      process(param)
  for result in distr.result:
    process(result)
  return res





