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
class ws_sample(ws_rtc_snap):
  def __init__(self, rdr):
    ws_rtc_snap.__init__(self, rdr)
    self.message = 'onExecute'

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

  def callOtherFunc(self, json_data):
    try:
      comp = self.rtcmgr.comp
      out_name = str(json_data['out_name'])
      message = str(json_data['message'])

      if comp._datatype[out_name] == 'RTC.TimedString' :
        data = instantiateDataType(TimedString)
        data.data = message
        comp._port[out_name].write(data)
      else:
        print "No match"
    except:
      print "ERROR"
      pass

    return

  def on_exec(self, ec_id):
    res=self.snap_broadcast(self.message, True, 0.5)
    if res is None:
      pass
    else:
      print res
    return


  def on_data_inport(self, port, data):
    name = self.rtcmgr.comp.findDataPort(port)
    if type(data.data) is str:
      res=self.snap_broadcast(data.data, True, 0.5)
    return

  def on_data_outport(self, port, data):
    #name = self.rtcmgr.comp.findDataPort(port)
    #print "Ouput to ", name, " ...", port.getPortDataType()
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

