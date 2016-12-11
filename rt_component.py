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

import time

import logging
import comm


#######
# OpenRTM-aist
import OpenRTM_aist
import omniORB
from RTC import *

###################
# Specification of RTC 
#
__version__ = "0.1"

rtcweb_spec = ["implementation_id", "RtcWeb",
               "type_name",         "RtcWeb",
               "description",       __doc__.encode('UTF-8'),
               "version",           __version__,
               "vendor",            "AIST",
               "category",          "RtcManger",
               "activity_type",     "DataFlowComponent",
               "max_instance",      "1",
               "language",          "Python",
               "lang_type",         "script",
               "conf.default.docroot_dir", "html/",
               "conf.default.project_dir", "project/",
               "exec_cxt.periodic.rate", "1",
               ""]

#########################################################################
#
# DataListener
#   This class connected with DataInPort
#
class RtcWebDataListener(OpenRTM_aist.ConnectorDataListenerT):
    def __init__(self, name, type, obj):
        self._name = name
        self._type = type
        self._obj = obj

    def __call__(self, info, cdrdata):
        data = OpenRTM_aist.ConnectorDataListenerT.__call__(self,
                        info, cdrdata, instantiateDataType(self._type))
        self._obj.onData(self._name, data)


###################
from RtcWeb_Core import *

###################
# RTC 
#

class RtcWeb(OpenRTM_aist.DataFlowComponentBase, RtcWeb_Core):
  def __init__(self, manager):
    OpenRTM_aist.DataFlowComponentBase.__init__(self, manager)
    RtcWeb_Core.__init__(self)
    self.manager = manager
    self.activated = False
    self.wevsocketAdaptor = None

    self._docroot_dir = ["html/"]
    self._project_dir = ["project/"]
    
  def exit(self):
    RtcWeb_Core.exit(self)
    OpenRTM_aist.DataFlowComponentBase.exit(self)

  def onInitialize(self):
    OpenRTM_aist.DataFlowComponentBase.onInitialize(self)
    self.bindParameter("docroot_dir", self._docroot_dir, "html/")
    self.bindParameter("project_dir", self._project_dir, "project/")

    return RTC_OK

  def onActivated(self, ec_id):
    self.activated = True
    return RTC_OK

  def onDeactivated(self, ec_id):
    self.activated = False
    return RTC_OK

  def onFinalize(self):
    OpenRTM_aist.DataFlowComponentBase.onFinalize(self)
    return RTC_OK

  def onShutdown(self, ec_id):
    return RTC_OK

  def onExecute(self, ec_id):
    OpenRTM_aist.DataFlowComponentBase.onExecute(self, ec_id)
    if self.websocketAdaptor :
      self.websocketAdaptor.snap_broadcast('Go')
       
    return RTC_OK

  def activate(self):
    execContexts = self.get_owned_contexts()
    execContexts[0].activate_component(self.getObjRef())

  def deactivate(self):
    execContexts = self.get_owned_contexts()
    execContexts[0].deactivate_component(self.getObjRef())

  def createInPort(self, name, type):
    if name in self._port.keys():
      print "DataPort '%s' already exists." % name
      return
    self._data[name] = instantiateDataType(type)
    self._datatype[name] = str(type)
    self._port[name] = OpenRTM_aist.InPort(name, self._data[name])

    self._port[name].addConnectorDataListener(
               OpenRTM_aist.ConnectorDataListenerType.ON_BUFFER_WRITE,
               RtcWebDataListener(name, type, self))

    self.registerInPort(name, self._port[name])

  def createOutPort(self, name, type):
    if name in self._port.keys():
      print "DataPort '%s' already exists." % name
      return
    self._data[name] = instantiateDataType(type)
    self._datatype[name] = str(type)
    self._port[name] = OpenRTM_aist.OutPort(name, self._data[name],
                              OpenRTM_aist.RingBuffer(8))
    self.registerOutPort(name, self._port[name])

  def delPort(self, name):
    port = self._port[name]
    if  port in self._inports : 
      self.removeInPort(port)
    elif  port in self._outports : 
      self.removeOutPort(port)
    else:
      print "No such dataport..."
      return
    del self._data[name]
    del self._datatype[name]
    del self._port[name]

  def setWebSocketAdaptor(self, ws):
    self.websocketAdaptor = ws

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
    self.manager=None
    self.comp=None
    self.comps=[]

    self.setWSCmd(ws)
    self.parseArgs()
    argv = self.other_args
    self.manager = OpenRTM_aist.Manager.init(argv)
    self.manager.setModuleInitProc(self.moduleInit)
    self.manager.activateManager()

  #
  #  Initialize the RtcWeb
  #
  def moduleInit(self, manager):
    profile = OpenRTM_aist.Properties(defaults_str=rtcweb_spec)
    manager.registerFactory(profile, RtcWeb, OpenRTM_aist.Delete)

  def createRtc(self, name="RtcWeb", ports=[]):
    comp = self.manager.createComponent(name)
    if comp == None:
      print "Fail to create component.",name
      return None
#      sys.exit(1)

    for prof in ports:
      if prof['type'] == 'in' :
        comp.createInPort(str(prof['name']), eval(prof['data_type']))

      elif prof.type == 'out':
        comp.createOutPort(str(prof['name']), eval(prof['data_type']))
      else:
        print "Port ",prof['type'], "isn't supported"

    comp.manager = self.manager
    self.comps.append(comp)

    return comp

  def setCurrentRtc(self, name):
    self.comp = None

    for comp in self.comps:
      if comp.getNamingNames() == name:
        self.comp = comp
        return self.comp

    return None

  #
  #
  #
  def addInPort(self, args):
    if self.comp is None:
      print "No component selected."
    else:
      self.comp.createInPort(str(args[0]), eval(args[1]))
    return

  #
  #
  #
  def addOutPort(self, args):
    if self.comp is None:
      print "No component selected."
    else:
      self.comp.createOutPort(str(args[0]), eval(args[1]))
    return
  #
  #
  #
  def addDataPort(self, args):
    if self.comp is None:
      print "No component selected."
    else:
      if args[0] == 'in': 
        self.comp.createInPort(str(args[1]), eval(args[2]))
      elif args[0] == 'out': 
        self.comp.createOutPort(str(args[1]), eval(args[2]))
      else:
        print "Invalid parameters."
    return

  def deleteDataPort(self, args):
    if self.comp is None:
      print "No component selected."
    else:
      print "delete data port..."
      self.comp.delPort(str(args[0]))
  #
  #
  #
  def activateRtc(self):
    if self.comp is None:
      print "No component selected."
    else:
      self.comp.activate()
  #
  #
  #
  def deactivateRtc(self):
    if self.comp is None:
      print "No component selected."
    else:
      self.comp.deactivate()
  #
  #
  #
  def setSnap(self, ws):
    if self.comp is None:
      print "No component selected."
    else:
      self.comp.setWebSocketAdaptor(ws)
  #
  #
  def setWSCmd(self, ws):
    self.ws = ws
    ws.rtcmgr = self

  def parseArgs(self):
    self.parser = argparse.ArgumentParser(description='Http server for WebSocket')
    self.parser.add_argument('-p','--port', action='store', default=self.port)
    self.parser.add_argument('-d', '--daemon', action='store_true', default='False')
    self.parser.add_argument('--ssl', action='store_true', default=self.ssl)
    self.parser.add_argument('--root', action='store', default=self.doc_root)
    self.parser.add_argument('--debug', action='store_true')
    self.parser.add_argument('--version', action='version', version='%(prog)s 0.1')
    (self.args, self.other_args) = self.parser.parse_known_args()


    self.port = int(self.args.port)
    self.doc_root = self.args.root
    self.ssl = self.args.ssl
  
    return self.args

  def start(self):
    self.manager.runManager(True)
    self.start_httpd()

  def start_httpd(self):
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
    comm.logger.info( "Server terminated." )
    for comp in self.comps:
      comp.exit()
    self.manager.shutdown()
    comm.logger.info( "...RTC Manager shutdown")
    self.server.close_service()
    self.server.terminate()
    comm.logger.info( " ...DONE")

  def listRtc(self):
    for comp in self.comps:
      print comp.getNamingName()

