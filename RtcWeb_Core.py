#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (C) 2009-2014
    Isao Hara
    Intelligent Systems Research Institute,
    National Institute of Advanced Industrial Science and Technology (AIST), Japan
    All rights reserved.
  Licensed under the MIT License (MIT)
  http://www.opensource.org/licenses/MIT
'''

############### import libraries
import sys
import os
import traceback
import subprocess

import time
import utils
import OpenRTM_aist
import omniORB
from RTC import *


#########################################################################
#
#  Class RtcWeb_Core
#
class RtcWeb_Core:
  def __init__(self):
    if hasattr(sys, "frozen"):
      self._basedir = os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding()))
    else:
      self._basedir = os.path.dirname(__file__)
#    self.parser = SEATML_Parser(self)
    self.states = []
    self.keys = {}
    self.regkeys = {}
    self.statestack = []
    self.currentstate = "start"
    self.adaptors = {}
    self.adaptortype = {}

    self._data = {}
    self._datatype = {}
    self._port = {}
    self.popen = []

    self.init_state = None
    self._scriptfile = ["None"]
    self.webServer = None
    self.root = None

  #
  #
  def exit(self):
    print  "Call RtcWeb_Core.exit"
    return

  ##### Create Adaptors
  #
  #  Create Adaptor, not use..
  #
  def createAdaptor(self, compname, tag):
    try:
      name = str(tag.get('name'))
      type = tag.get('type')
      self._logger.info(u"createAdaptor: " + type + ": " + name)

      return -1
    except:
      self._logger.error(u"invalid parameters: " + type + ": " + name)
      return -1

    return 1

  ###########################
  # Send Data 
  #
  def send(self, name, data, code='utf-8'):
    if isinstance(data, str) :
      self._logger.info("sending message %s (to %s)" % (data, name))
    else:
      self._logger.info("sending message to %s" % (name,))

    dtype = self.adaptortype[name][1]

    if self.adaptortype[name][2]:
      ndata = []

      if type(data) == str :
        for d in data.split(","):
          ndata.append( convertDataType(dtype, d, code) )
        self._data[name].data = ndata
      else:
        self._data[name] = data

    elif dtype == str:
      self._data[name].data = data.encode(code)

    elif dtype == unicode:
      self._logger.info("sending message to %s, %s" % (data,code))
      self._data[name].data = unicode(data)

    elif dtype == int or dtype == float :
      self._data[name].data = dtype(data)

    else:
      try:
        if type(data) == str :
          self._data[name] = apply(dtype, eval(data))
        else:
          self._data[name] = data
      except:
        self._logger.error( "ERROR in send: %s %s" % (name , data))

    try:
      self._port[name].write(self._data[name])
    except:
      self._logger.error("Fail to sending message to %s" % (name,))

  ##################################
  #  Event processes 
  #
  #  onData: this method called in comming data
  #
  def onData(self, name, data):
    try:
      if isinstance(data, str):
        if data :
          data2 = parseData(data)
          if data2 :
            self.processOnDataIn(name, data2)
          else :
            self.processOnDataIn(name, data)
        else:
          self.processOnDataIn(name, data)
    except:
      self._logger.error(traceback.format_exc())

  #
  #   main event process 
  #

  #
  # process for the cyclic execution
  #
  def processExec(self, sname=None, flag=False):
    if sname is None : sname = self.currentstate
    cmds = self.lookupWithDefault(sname, '', 'onexec', False)

    if not cmds :
      if flag :
        self._logger.info("no command found")
      return False

    #
    #
    for c in cmds:
      self.activateCommand(c, '')
    return True

  #
  #  Event process for data-in-event
  def processOnDataIn(self, name, data):
    self._logger.info("got input from %s" %  (name,))
    cmds = self.lookupWithDefault(self.currentstate, name, "ondata")

    if not cmds:
      self._logger.info("no command found")
      return False

    for c in cmds:
      kond = c[0]
      globals()['rtc_in_data'] = data
      if kond[0] :
        ffname = utils.findfile(kond[0])
        if ffname :
          execfile(ffname, globals())
#        execfile(kond[0], globals())

      if eval(kond[1], globals()):
        for cmd in c[1]:
          self.activateCommandEx(cmd, data)
    return True

  #
  #  Lookup Registered Commands with default
  #
  def lookupWithDefault(self, state, name, s, flag=True):
    s=s.split(",")[0]
    if flag:
      self._logger.info('looking up...%s: %s' % (name,s,))
    cmds = self.lookupCommand(state, name, s)

    if not cmds:
      cmds = self.lookupCommand(state, 'default', s)

    if not cmds:
      cmds = self.lookupCommand('all', name, s)

    if not cmds:
      cmds = self.lookupCommand('all', 'default', s)

    return cmds

  #
  #  Lookup Registered Commands
  #
  def lookupCommand(self, state, name, s):
    cmds = []
    regkeys = []
    try:
      cmds = self.keys[state+":"+name+":"+s]
    except KeyError:
      try:
        regkeys = self.regkeys[state+":"+name]
      except KeyError:
        return None

      for r in regkeys:
        if r[0].match(s):
          cmds = r[1]
          break
      return None
    return cmds

  #############################
  #  For STATE 
  #
  #  Get state infomation
  #
  def getStates(self):
    return self.states

  #
  # set the begining state
  #
  def setStartState(self, name):
    self.startstate = name
    return

  #
  #  Count the number of states 
  #
  def countStates(self):
    return len(self.states)

  #
  #  check the named state
  #
  def inStates(self, name):
    return ( self.states.count(name) > 0 )

  #
  #  append the named state
  #
  def appendState(self, name):
    self.states.extend([name])
    return

  #
  #  initilaize the begining state
  #
  def initStartState(self, name):
    self.startstate = None
    if self.states.count(name) > 0 :
      self.startstate = name
    else:
      self.startstate = self.states[0]
    self.stateTransfer(self.startstate)
    self._logger.info("current state " + self.currentstate)

  #
  # create the named state
  #
  def create_state(self, name):
    self.items[name] = []
    if self.init_state == None:
      self.init_state = name
    return 

  ###############################################
  # State Transition for eSEAT
  #
  def stateTransfer(self, newstate):
    try:
      for c in self.keys[self.currentstate+":::onexit"]:
        self.activateCommand(c)
    except KeyError:
      pass

    try:
      self.prev_state=self.currentstate
      self.next_state=newstate
      self.root.event_generate("<<state_transfer>>", when="tail")
    except:
      pass

    self.currentstate = newstate

    try:
      for c in self.keys[self.currentstate+":::onentry"]:
        self.activateCommand(c)
    except KeyError:
      pass

  ############ T A G Operations
  #
  #  Execute <message>
  #
  def applyMessage(self, c):
    name = c[1]
    data = c[2]
    encoding = c[3]
    input_id = c[4]

    try:
      ad = self.adaptors[name]
      if input_id :
        if self.inputvar.has_key(input_id) :
          data = self.inputvar[input_id].get()
        elif self.stext.has_key(input_id) :
          data = self.getLastLine(input_id, 1)

      #
      #  Call 'send' method of Adaptor
      #
      if not encoding :
        ad.send(name, data)
      else :
         ad.send(name, data, encoding)
          #ad.send(host, data.encode(c[3]))

    except KeyError:
      if name :
        self._logger.error("no such adaptor:" + name)
      else :
        self._logger.error("no such adaptor: None")

  #
  #  Execute <statetransition>
  #
  def applyTransition(self, c):
    func,data = c[1:]

    if (func == "push"):
      self.statestack.append(self.currentstate)
      self.stateTransfer(data)

    elif (func == "pop"):
      if self.statestack.__len__() == 0:
        self._logger.warn("state buffer is empty")
        return
      self.stateTransfer(self.statestack.pop())

    else:
      self._logger.info("state transition from "+self.currentstate+" to "+data)
      self.stateTransfer(data)

  #
  #  Execute <log>
  #
  def applyLog(self, c):
    data = c[1]
    self._logger.info(data)

  #
  #  Execute <shell>
  #
  def applyShell(self, c):
    name ,data = c[1:]
    #
    # execute shell command with subprocess
    res = subprocess.Popen(data, shell=True)
    self.popen.append(res)

    #
    #  Call 'send' method of Adaptor
    try:
      ad = self.adaptors[name]
      ad.send(name, res)
    except KeyError:
      if name :
       self._logger.error("no such adaptor:" + name)
      else:
       self._logger.error("no such adaptor: None")

  #
  #  Execute <script>
  #
  def applyScript(self, c, indata=None):
    name,data,fname = c[1:]

    globals()['rtc_result'] = None
    globals()['rtc_in_data'] = indata
    globals()['web_in_data'] = indata

    #
    #   execute script or script file
    if fname :
      ffname = utils.findfile(fname)
      if ffname :
        execfile(ffname,globals())
    try:
      if data :
        exec(data, globals())
    except:
      print data
      #self._logger.error("Fail to execute script:" + name)

    # 
    #  Call 'send' method of Adaptor to send the result...
    rtc_result = globals()['rtc_result'] 
    if rtc_result == None :
      pass
    else:
      try:
        ad = self.adaptors[name]
        ad.send(name, rtc_result)
      except KeyError:
        if name :
          self._logger.error("no such adaptor:" + name)
        else:
          self._logger.error("no such adaptor: None")

  ########################
  #
  #  Activate Lookuped Commands
  #
  def activateCommand(self, c, data=None):
    if   c[0] == 'c': self.applyMessage(c)
    elif c[0] == 'l': self.applyLog(c)
    elif c[0] == 'x': self.applyShell(c)
    elif c[0] == 's': self.applyScript(c, data)
    elif c[0] == 't': self.applyTransition(c)

  #
  #
  def activateCommandEx(self, c, data):
    if c[0] == 'c': c[3] = None
    self.activateCommand(c, data)

  ##############################
  #  main  loader
  #
  def loadXML(self, f):
    self._logger.info("Start loadXML:"+f)
    res = self.parser.load(f)
    if res == 1 : 
      self._logger.error("===> XML Parser error")
      if self.manager : self.manager.shutdown()
      sys.exit(1)

  #
  #  register commands into self.keys
  #
  def registerCommands(self, key, cmds):
    self._logger.info("register key="+key)
    self.keys[key] = cmds

  def appendCommands(self, key, cmds):
    self._logger.info(" append key="+key)
    self.keys[key].append(cmds) 

  def registerCommandArray(self, tag, cmds):
    if self.keys.keys().count(tag) == 0 :
      self.registerCommands(tag, [cmds])
    else :
      self.appendCommands(tag, cmds)

  ##############################################
  #  Callback function for WebAdaptor
  #     
  def callComet(self):
    res = ""
    return res

  ################################################ 
  #
  #  Sub-process
  #
  def getSubprocessList(self):
    res=[]
    newlst=[]
    for p in self.popen:
      p.poll()
      if p.returncode == None:
        res.append(p.pid)
        newlst.append(p)
    self.popen = newlst
    return res

  #
  #
  #
  def killSubprocess(self, pid=None):
    for p in self.popen:
      p.poll()
      if pid == None or p.pid == pid :
        p.terminate()
    return 

  #
  # Finalize
  #
  def finalizeRTC(self):
    if self.root : self.root.quit()
    return 


#########################################################################
#   F U N C T I O N S
#
#  DataType for CORBA
#
def instantiateDataType(dtype):
    if isinstance(dtype, int) : desc = [dtype]
    elif isinstance(dtype, tuple) : desc = dtype
    else : 
        desc=omniORB.findType(dtype._NP_RepositoryId) 

    if desc[0] in [omniORB.tcInternal.tv_alias ]: return instantiateDataType(desc[2])

    if desc[0] in [omniORB.tcInternal.tv_short, 
                   omniORB.tcInternal.tv_long, 
                   omniORB.tcInternal.tv_ushort, 
                   omniORB.tcInternal.tv_ulong,
                   omniORB.tcInternal.tv_boolean,
                   omniORB.tcInternal.tv_char,
                   omniORB.tcInternal.tv_octet,
                   omniORB.tcInternal.tv_longlong,
                   omniORB.tcInternal.tv_enum
                  ]: return 0

    if desc[0] in [omniORB.tcInternal.tv_float, 
                   omniORB.tcInternal.tv_double,
                   omniORB.tcInternal.tv_longdouble
                  ]: return 0.0

    if desc[0] in [omniORB.tcInternal.tv_sequence, 
                   omniORB.tcInternal.tv_array,
                  ]: return []


    if desc[0] in [omniORB.tcInternal.tv_string ]: return ""
    if desc[0] in [omniORB.tcInternal.tv_wstring,
                   omniORB.tcInternal.tv_wchar
                  ]: return u""

    if desc[0] == omniORB.tcInternal.tv_struct:
        arg = []
        for i in  range(4, len(desc), 2):
            attr = desc[i]
            attr_type = desc[i+1]
            arg.append(instantiateDataType(attr_type))
        return desc[1](*arg)
    return None

