import algprob
from defmodel import export, PythonDistributionSystem
from distribution import CallRef, DistrCall, Distribution, LiteralRef
from model import DistrResult, Model, WrappedModel
from proof import ProbLabel, Proof, ProofVar, VariableMapping
from sample import sample
from proofenv import evaluateProof

class TestDistributionSystem(PythonDistributionSystem):

  @export
  def biasFromBool(self, v, arg):
    return 0.85 if arg else 0.15

  @export
  def decideBias(self, v):
    v.chance = self.bernouli(0.5)
    v.result = self.biasFromBool(v.chance)
    return v.result

  @export
  def makeList(self, v, *args):
    return list(args)

  @export
  def flipWithBias(self, v, nflips, bias):
    for i in range(nflips):
      v['flip' + str(i)] = self.bernouli(bias)
    v.result = self.makeList(*[v['flip' + str(i)] for i in range(nflips)])
    return v.result


  @export
  def main(self):
    v.bias = self.decideBias()
    v.result = self.flipWithBias(20, v.bias)
    return v.result

def testSample():
  model = WrappedModel(TestDistributionSystem().getModel())
  print(model.getDistribution(DistrCall('decideBias', [])))
  for i in range(20):
    res = sample(model, DistrCall('main', []))
    print(res)
    print(list(map(model.refToJSON, res)))

def testProof():
  model = WrappedModel(TestDistributionSystem().getModel())
  call = DistrCall('decideBias', [])
  half = model.JSONToRef(0.5)
  true = model.JSONToRef(True)
  false = model.JSONToRef(False)
  highBias = model.JSONToRef(0.85)

  bernouliCall = DistrCall('bernouli', [half])
  bernouliLabel = ProbLabel(bernouliCall, [true])
  decideBiasCall = DistrCall('decideBias', [])
  biasTrueCall = DistrCall('biasFromBool', [true])
  decideBiasLabel = ProbLabel(decideBiasCall, [highBias])
  biasTrueLabel = ProbLabel(biasTrueCall, [highBias])

  biasTrueProof = Proof(biasTrueLabel, [
    VariableMapping({})
  ])

  decideBiasProof = Proof(decideBiasLabel, [
    VariableMapping({'chance': true, 'result': highBias})
  ])
  res = evaluateProof(model, [decideBiasProof, biasTrueProof], 0)
  print(res)

testProof()
