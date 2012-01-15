import json
import socket
import time

from distribution import Distribution, LiteralRef
from model import DistributionResult, Model


class SocketModelClient(Model):

  BUFSIZE = 1024

  def __init__(self, sock):
    self.socket = sock

  def rawQueryModel(self, queryString):
    self.socket.sendAll(queryString)
    data = ""
    while True:
      resp = self.socket.recv(SocketModel.BUFSIZE)
      data += resp
      if '\n' in resp:
        break
      time.sleep(0)
    return json.loads(data)

  def queryModel(self, command, args):
    query = command + ' ' + json.dumps(args)
    return self.rawQueryModel(query)

  def getDistribution(self, call):
    res = self.queryModel('getDistribution', call.toJSON())
    return DistributionResult.fromJSON(res)

  def modifyReferenceCount(self, ref, delta):
    self.queryModel(
      'modifyReferenceCount', {
        'ref': ref.toJSON(),
        'delta': delta
      }
    )

  def readJSON(self, jsonObj):
    res = self.queryModel('readJSON', jsonObj)
    return LiteralRef.fromJSON(res)

  def writeJSON(self, ref):
    return self.queryModel('writeJSON', ref.toJSON())

  def isEqual(self, aref, bref):
    return self.queryModel('isEqual', [aref.toJSON(), bref.toJSON()])




