
import comm

class ws_sample(comm.WebSocketCommand):
  def __init__(self, rdr):
    comm.WebSocketCommand.__init__(self, rdr, "")

  def chat(self, msg):
    if msg == "bye":
      self.sendCloseFrame()
    else:
      msg = "Reply:"+msg
      self.sendTextFrame(msg)
    return

  def json(self, msg):
    services = self.getServices()
    for srv in services:
      ws = srv.reader.command
      if isinstance(ws,WebSocketCommand):
        if ws != self:
          ws.sendTextFrame(msg)
        else:
          pass
    return

  def blob(self, msg):
    res="Upload: %d bytes" % len(msg)
    print res
    self.sendTextFrame(res)
    return

  def rpc(self, msg):
    res="alert('%s');" % msg
    print res
    self.sendTextFrame(res)
    return



if __name__ == '__main__' :
  reader = comm.HttpReader(None, "html")
  reader.WSCommand = ws_sample(reader)
  srv = comm.SocketServer(reader, "Web", "localhost", 8080, False)
  srv.start()

