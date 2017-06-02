import os
import json
import sys
import yaml
import comm

####
##


####
##  Sample WS commander
class ws_sample(comm.WebSocketCommand):
  def __init__(self, rdr):
    comm.WebSocketCommand.__init__(self, rdr, "")

  def json(self, msg):
    wslist = self.getWSList()
    for ws in wslist:
      if ws != self:
        ws.sendDataFrame(msg)
      else:
        pass
    return

###################
def main():
    global srv
    srv = comm.create_httpd(8080, "Y:\html", ws_sample)
    srv.start()
    return srv

if __name__ == '__main__' :
  main()

