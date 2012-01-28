import algprob
from defmodel import export, PythonDistributionSystem
from distribution import CallRef, DistrCall, Distribution, LiteralRef
from model import DistrResult, Model, WrappedModel
from proof import LetProof, ProbLabel, Proof, ReturnProof, Variable
from sample import sample
from proofsystem import evaluateProof

class TestDistributionSystem(PythonDistributionSystem):

  @export
  def biasFromBool(self, arg):
    return 0.15 if arg else 0.85

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
  biasCall = DistrCall('decideBias', [])
  biasTrueCall = DistrCall('biasFromBool', [true])
  biasLabel = ProbLabel(biasCall, [highBias])
  biasTrueLabel = ProbLabel(biasTrueCall, [highBias])
  biasTrueProof = LetProof(
    ReturnProof([highBias])
  )

  biasProof = LetProof(
    DistrCall('bernouli', [half]), {
      (true,): LetProof(
        biasCall, {
          (highBias,): ReturnProof([highBias])
        }
      )
    }
  )

testProof()
