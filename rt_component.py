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
import OpenRTM_aist
import omniORB
from RTC import *

###################
# RTC 
#
class RtcWeb(OpenRTM_aist.DataFlowComponentBase):
  def __init__(self, manager):
    OpenRTM_aist.DataFlowComponentBase.__init__(self, manager)
    
  def exit(self):
    OpenRTM_aist.DataFlowComponentBase.exit(self)

###################
# RTC Manager
#
class rtc_manager:
  def __init__(self, ws=None):
    self.port=8080
    self.doc_root="html"
    self.daemon=False
    self.ssl=False
    self.debug=False

    self.setWSCmd(ws)
    self.parseArgs()

  def setWSCmd(self, ws):
    self.ws = ws

  def parseArgs(self):
    self.parser = argparse.ArgumentParser(description='Http server for WebSocket')
    self.parser.add_argument('-p','--port', action='store', default=self.port)
    self.parser.add_argument('-d', '--daemon', action='store_true', default='False')
    self.parser.add_argument('--ssl', action='store_true', default=self.ssl)
    self.parser.add_argument('--root', action='store', default=self.doc_root)
    self.parser.add_argument('--debug', action='store_true')
    self.parser.add_argument('--version', action='version', version='%(prog)s 0.1')
    self.args = self.parser.parse_args()

    self.port = int(self.args.port)
    self.doc_root = self.args.root
    self.ssl = self.args.ssl
    return self.args

  def start(self):
    self.server = comm.create_httpd(self.port, self.doc_root, self.ws, "", self.ssl)

    if self.daemon == True :
      comm.logger.info( "Start as daemon" )
      comm.daemonize()
    else:
      pass

    if self.debug == True:
      comm.logger.setLevel(logging.DEBUG)
    self.server.start()

    return self.server

  def exit(self):
    self.server.close_service()
    self.server.terminate()


#
#
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

