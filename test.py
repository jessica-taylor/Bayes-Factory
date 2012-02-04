import algprob
from defmodel import export, PythonDistributionSystem
from distribution import CallRef, DistrCall, Distribution, LiteralRef
from model import DistrResult, Model, WrappedModel
from proof import ProbLabel, Proof, Variable
from sample import sample
from proofsystem import evaluateProof

class TestDistributionSystem(PythonDistributionSystem):

  @export
  def biasFromBool(self, arg):
    return 0.85 if arg else 0.15

  @export
  def decideBias(self):
    return self.biasFromBool(self.bernouli(0.5))

  @export
  def makeList(self, *args):
    return list(args)

  @export
  def flipWithBias(self, nflips, bias):
    return self.makeList(*[self.bernouli(bias) for i in range(nflips)])

  @export
  def main(self):
    return self.flipWithBias(20, self.decideBias())

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
  biasTrueProof = Proof(biasTrueLabel, [[]])
  decideBiasProof = Proof(
    decideBiasLabel, [
      [bernouliLabel, biasTrueLabel]
    ]
  )
  res = evaluateProof(model, [decideBiasProof, biasTrueProof], 0)
  print(res)

testProof()
