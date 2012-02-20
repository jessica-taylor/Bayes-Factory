from collections import defaultdict
import math
import numbers
import random

import graphsort

from distribution import DistrCall, Distribution, LiteralRef, LocalVariable
from model import DistrResult, Model


def resolveValue(values, val):
  if isinstance(val, LocalVariable):
    return values[val.name]
  return val

def resolveCall(values, call):
  return DistrCall(call.function, tuple(resolveValue(values, v) for v in call.parameters))

def addValues(values, variables, result):
  result = list(result)
  variables = list(variables)
  assert len(result) == len(variables)
  for v,r in zip(variables, result):
    values[v] = r


# def distributionLiteralRefs(distr):
#   res = []
#   def process(value):
#     if isinstance(value, LiteralRef):
#       res.append(value)
#   for call in distr.calls:
#     for param in call.parameters:
#       process(param)
#   for result in distr.result:
#     process(result)
#   return res





