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


from types import *
#######
# OpenRTM-aist
#import rt_component as rtc
from rt_component import *

#
#  WebSocketCommand
#
class ws_sample(comm.WebSocketCommand):
  def __init__(self, rdr):
    comm.WebSocketCommand.__init__(self, rdr, "")

  def init(self, f):
    if f == 'rpc':
      self.rtcmgr.setSnap(self)

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
    if type(msg) is StringType or type(msg) is UnicodeType:
      cmd = msg

    elif type(msg) is ListType:
      cmd = msg.pop(0)

    else:
      self.logger.error( "Invalid message" )
      return

    self.logger.info( "Call rpc:"+cmd )
    
    try:
      if cmd == 'createRtc':
        comp=self.rtcmgr.createRtc('RtcWeb', msg)
        if comp :
          comp.setWebSocketAdaptor(self)

      elif cmd == 'getRtcList':
        rtclist = []
        for comp in self.rtcmgr.comps :
          data={}
          data['name']=comp.getNamingNames()[0]
          inp_data=[]
          
          for inp in comp._inports:
            pdata={}
            pdata['name'] = inp._name
            pdata['data_type'] = comp._datatype[inp._name]
            inp_data.append( pdata )

          data['in_port'] = inp_data

          outp_data=[]
          for outp in comp._outports:
            pdata={}
            pdata['name'] = outp._name
            pdata['data_type'] = comp._datatype[outp._name]
            outp_data.append( pdata )

          data['out_port'] = outp_data
          rtclist.append( data )

        self.sendDataFrame(json.dumps({'reply_seq':seq, 'result': rtclist}))

      elif cmd == 'setCurrentRtc':
        self.rtcmgr.setCurrentRtc(msg)
 
      elif cmd == 'addDataPort':
        self.rtcmgr.addDataPort(msg)

      elif cmd == 'deleteDataPort':
        self.rtcmgr.deleteDataPort(msg)

      elif cmd == 'activateRtc':
        self.rtcmgr.activateRtc()

      elif cmd == 'deactivateRtc':
        self.rtcmgr.deactivateRtc()

      elif cmd == 'projects':
        flist = os.listdir(self.reader.dirname +'/snap/projects')
        flist.sort()
        self.sendDataFrame(json.dumps({'reply_seq':seq, 'result': flist}))

      elif cmd == 'exit':
        self.sendDataFrame(json.dumps({'reply_seq':seq, 'result': 'close'}))
        self.rtcmgr.exit()

    except:
      self.logger.error( "catch exception in ws_sample.rpc " +cmd)
    return

  def rtmgr(self, msg, seq):
    if type(msg) is StringType or type(msg) is UnicodeType:
      cmd = msg

    elif type(msg) is ListType:
      cmd = msg.pop(0)

    else:
      self.logger.error( "Invalid message" )
      return

    self.logger.info( "Call rpc:"+cmd )
    
    try:
      if cmd == 'createRtc':
        comp=self.rtcmgr.createRtc('RtcWeb', msg)
        if comp :
          comp.setWebSocketAdaptor(self)

      elif cmd == 'getRtcList':
        rtclist = []
        for comp in self.rtcmgr.comps :
          data={}
          data['name']=comp.getNamingNames()[0]
          inp_data=[]
          
          for inp in comp._inports:
            pdata={}
            pdata['name'] = inp._name
            pdata['data_type'] = comp._datatype[inp._name]
            inp_data.append( pdata )

          data['in_port'] = inp_data

          outp_data=[]
          for outp in comp._outports:
            pdata={}
            pdata['name'] = outp._name
            pdata['data_type'] = comp._datatype[outp._name]
            outp_data.append( pdata )

          data['out_port'] = outp_data
          rtclist.append( data )

        self.sendDataFrame(json.dumps({'reply_seq':seq, 'result': rtclist}))

      elif cmd == 'setCurrentRtc':
        self.rtcmgr.setCurrentRtc(msg)
 
      elif cmd == 'addDataPort':
        self.rtcmgr.addDataPort(msg)

      elif cmd == 'deleteDataPort':
        self.rtcmgr.deleteDataPort(msg)

      elif cmd == 'activateRtc':
        self.rtcmgr.activateRtc()

      elif cmd == 'deactivateRtc':
        self.rtcmgr.deactivateRtc()

      elif cmd == 'projects':
        flist = os.listdir(self.reader.dirname +'/snap/projects')
        flist.sort()
        self.sendDataFrame(json.dumps({'reply_seq':seq, 'result': flist}))

      elif cmd == 'exit':
        self.sendDataFrame(json.dumps({'reply_seq':seq, 'result': 'close'}))
        self.rtcmgr.exit()

    except:
      self.logger.error( "catch exception in ws_sample.rpc " +cmd)
    return


###################
# Global functions
#
def exit():
  global mgr
  mgr.exit()

if __name__ == '__main__' :
  mgr = rtc_manager(ws_sample)
  mgr.start()

