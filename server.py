import os
import sys
import json
import comm

class ws_sample(comm.WebSocketCommand):
  def __init__(self, rdr):
    comm.WebSocketCommand.__init__(self, rdr, "")

  def chat(self, msg, seq=-1):
    if msg == "bye":
      self.sendCloseFrame()
    else:
      msg = "Reply:"+msg
      self.sendDataFrame(msg)
    return

  def json(self, msg, seq=-1):
    wslist = self.getWSList()
    for ws in wslist:
      if ws != self:
        ws.sendDataFrame(msg)
      else:
        pass
    return

  def blob(self, msg, seq=-1):
    res="Upload: %d bytes" % len(msg)
    print res
    self.sendDataFrame(res)
    return

  def rpc(self, msg, seq):
    try:
      if msg == 'projects':
        flist = os.listdir(self.reader.dirname +'/snap/projects')
        flist.sort()
        self.sendDataFrame(json.dumps({'reply_seq':seq, 'result': flist}))
      if msg == 'exit':
        self.sendDataFrame(json.dumps({'reply_seq':seq, 'result': 'close'}))
        exit()
    except:
      print "ERROR in rpc"
    return

###################
def exit():
    global srv
    srv.terminate()
    sys.exit()

def main():
    global srv
    srv = comm.create_httpd(8080, "html", ws_sample, "")
    comm.daemonize()
    srv.start()
    return srv

if __name__ == '__main__' :
  srv=main()
#  comm.daemonize()

