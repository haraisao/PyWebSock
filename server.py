
import comm

class ws_sample(comm.WebSocketCommand):
  def __init__(self, rdr):
    comm.WebSocketCommand.__init__(self, rdr, "")

  def chat(self, msg):
    if msg == "bye":
      self.sendCloseFrame()
    else:
      msg = "Reply:"+msg
      self.sendDataFrame(msg)
    return

  def json(self, msg):
    wslist = self.getWSList()
    for ws in wslist:
      if ws != self:
        ws.sendDataFrame(msg)
      else:
        pass
    return

  def blob(self, msg):
    res="Upload: %d bytes" % len(msg)
    print res
    self.sendDataFrame(res)
    return

  def rpc(self, msg):
    res="alert('%s');" % msg
    print res
    #self.sendDataFrame(res)
    return

###################
def main():
    global srv
    srv = comm.create_httpd(8080, "html", ws_sample)
    srv.start()
    return srv

if __name__ == '__main__' :
  main()

