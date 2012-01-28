
from collections import defaultdict
import math
import numbers
import random

from distribution import CallRef, DistrCall, Distribution, LiteralRef
from model import DistrResult, Model

import algprob

def sampleDistr(model, distribution):
  assert isinstance(model, Model)
  assert isinstance(distribution, Distribution)
  values = []
  for call in distribution.calls:
    resolvedCall = algprob.resolveCall(values, call)
    values.append(sample(model, resolvedCall))
  return tuple(resolveValue(values, r) for r in distribution.result)


def sample(model, call):
  assert isinstance(model, Model)
  assert isinstance(call, DistrCall)
  if call.function == 'bernouli':
    assert len(call.parameters) == 1
    p = model.refToJSON(call.parameters[0])
    assert isinstance(p, numbers.Real)
    assert 0 <= p <= 1
    model.modifyReferenceCount(call.parameters[0], -1)
    res = random.random() < p
    return [model.JSONToRef(res)]
  distrResult = model.getDistribution(call)
  res = sampleDistr(model, distrResult.distribution)
  return res
