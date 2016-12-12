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

  def on_exec(self, ec_id):
    self.snap_broadcast('onExecute')

###################
# Global functions
#
def exit():
  global mgr
  mgr.exit()

if __name__ == '__main__' :
  mgr = rtc_manager(ws_sample)
  mgr.start()

