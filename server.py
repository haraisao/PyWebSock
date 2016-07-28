#
#
#
import os
import sys
import json
import argparse

import logging
import comm

#
#  WebSocketCommand
#
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
      self.logger.error( "catch exception in ws_sample.rpc" )
    return

###################
# Global functions
#
def exit():
    global srv
    srv.close_service()
    srv.terminate()

def main(port=8080, doc_root="html", daemon=False, ssl=False, debug=False):
    global srv
    srv = comm.create_httpd(port, doc_root, ws_sample, "", ssl)

    if daemon == True :
      comm.logger.info( "Start as daemon" )
      comm.daemonize()
    else:
      pass

    if debug==True:
      comm.logger.setLevel(logging.DEBUG)
    srv.start()
    return srv

if __name__ == '__main__' :
  parser = argparse.ArgumentParser(description='Http server for WebSocket')
  parser.add_argument('-p','--port', action='store', default=8080)
  parser.add_argument('-d', '--daemon', action='store_true', default='False')
  parser.add_argument('--ssl', action='store_true', default='False')
  parser.add_argument('--root', action='store', default='html')
  parser.add_argument('--debug', action='store_true')
  parser.add_argument('--version', action='version', version='%(prog)s 0.1')
  args = parser.parse_args()

  srv=main(int(args.port), args.root, args.daemon, args.ssl, args.debug)

