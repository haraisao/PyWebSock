#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
'''
  Copyright (C) 2016
     Isao Hara
     Robot Innovation Research Center
     National Institute of Advanced Industrial Science and Technology (AIST), Japan

     All rights reserved.
     Licensed under the MIT License(MIT)
     http://www.opensouce.org/license/MIT
'''
######################
#
#

import os
import sys
import json
import argparse

import logging
import comm


#######
# OpenRTM-aist
import rt_component as rtc

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
  mgr=rtc.rtc_manager(ws_sample)
  srv=mgr.start()

