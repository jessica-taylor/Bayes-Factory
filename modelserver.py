import json
import socket
import time

from distribution import Distribution, DistrCall, LiteralRef
from model import Model

class SocketModelServer:
  """
  Serves a model through a socket, so a SocketModelClient can communicate with it.
  """

  BUFSIZE = 1024

  def __init__(self, model, sock):
    self.model = model
    self.socket = sock

  def run(self):
    """
    Runs the server.
    """
    query = ""
    while True:
      received = self.socket.recv(SocketModelServer.BUFSIZE)
      query += received
      if '\n' in received:
        self.doQuery(query)
        query = ""
      time.sleep(0)


  def getQueryResult(self, query):
    split = query.find(' ')
    assert split != -1
    command = query[0 : split]
    jsonObj = json.loads(query[split + 1 :])
    if command == 'getDistribution':
      call = DistrCall.fromJSON(jsonObj)
      return self.model.getDistribution(call).toJSON()
    if command == 'modifyReferenceCount':
      ref = jsonObj['ref']
      delta = jsonObj['delta']
      self.model.modifyReferenceCount(ref, delta)
      return None
    if command == 'readJSON':
      return self.model.readJSON(jsonObj).toJSON()
    if command == 'writeJSON':
      return self.model.writeJSON(LiteralRef.fromJSON(jsonObj))
    if command == 'isEqual':
      return self.model.isEqual(jsonObj[0], jsonObj[1])

  def doQuery(self, query):
    res = self.getQueryResult(query)
    self.socket.sendAll(json.dumps(res) + '\n')




