#
#  PyWebScok Library
#  Communication Adaptor for WebSocket
#
#   Copyright(C) 2015, Isao Hara, AIST
#   Release under the MIT License.
#

import sys
import os
import socket
import select
import time
import datetime
import threading
import struct
import copy
import json

#
# Raw Socket Adaptor
#
#   threading.Tread <--- SocketPort
#
class SocketPort(threading.Thread):
  def __init__(self, reader, name, host, port):
    threading.Thread.__init__(self)
    self.reader = reader
    if self.reader:
      self.reader.setOwner(self)
    self.name = name
    self.host = host
    self.port = port
    self.socket = None
    self.service = []
    self.service_id = 0
    self.client_adaptor = True
    self.server_adaptor = None
    self.mainloop = False
    self.debug = False
  #
  #
  #
  def setHost(self, name):
    self.host = name
    return 

  def setPort(self, port):
    self.port = port
    return 

  def setClientMode(self):
    self.client_adaptor = True
    return 

  def setServerMode(self):
    self.client_adaptor = False
    return 

  #
  #
  #
  def setServer(self, srv):
    self.server_adaptor = srv
    return 
  #
  #
  #
  def getParser(self):
    return self.reader.parser
  #
  # Bind
  #
  def bind(self):
    try:
      self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.socket.bind((self.host, self.port))

    except socket.error:
      print "Connection error"
      self.close()
      return 0
    except:
      print "Error in connect " , self.host, self.port
      self.close()
      return -1

    return 1

  #
  # Connect
  #
  def connect(self, async=True):
    if self.mainloop :
      return 1

    try:
      self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.socket.connect((self.host, self.port))

    except socket.error:
      print "Connection error"
      self.close()
      return 0

    except:
      print "Error in connect " , self.host, self.port
      self.close()
      return -1

    if async :
      print "Start read thread ",self.name
      self.start()

    return 1

  #
  #  Wait for comming data...
  #
  def wait_for_read(self, timeout=0.1):
    try:
      rready, wready, xready = select.select([self.socket],[],[], timeout)
      if len(rready) :
        return 1
      return 0
    except:
      self.terminate()
      return -1

  #
  # Receive
  #
  def receive_data(self, bufsize=8192, timeout=1.0):
    data = None
    try:
      if self.wait_for_read(timeout) == 1  :
        data = self.socket.recv(bufsize)     # buffer size = 1024 * 8
        if len(data) != 0:
          return data
        else:
          return  -1

    except socket.error:
      print "socket.error in receive_data"
      self.terminate()

    except:
      self.terminate()

    return data

  #
  #  Thread oprations...
  #
  def start(self):
    self.mainloop = True
    threading.Thread.start(self)

  def run(self):
    if self.client_adaptor: 
      self.message_receiver()
    else:
      self.accept_service_loop()

  def remove_service(self, adaptor):
     try:
       self.service.remove(adaptor)
     except:
       pass

  #
  #
  #
  def accept_service_loop(self, lno=5, timeout=1.0):
    print "No accept_service_loop defined"

    return 

  #
  #  Background job ( message receiver )
  #
  def message_receiver(self):
    while self.mainloop:
      data = self.receive_data() 

      if data  == -1:
        self.terminate()

      elif data :
        self.reader.parse(data)

      elif data is None :
        pass

      else :
        print "Umm...:",self.name
        print data

#    print "Read thread terminated:",self.name

  #
  #  close socket
  #
  def close_service(self):
    for s in  self.service :
      s.terminate()

  def close(self):
    while self.service:
      self.service.pop().close()

    if self.server_adaptor:
      self.server_adaptor.remove_service(self)

    if self.socket :
      self.socket.close()
      self.socket = None

  #
  #  Stop background job
  #
  def terminate(self):
    self.mainloop = False
    self.close()

  #
  #  Send message
  #
  def send(self, msg, name=None):
    if not self.socket :
      print "Error: Not connected"
      return None
    try:
      self.socket.sendall(msg)

    except socket.error:
      print "Socket error in send"
      self.close()

#
#  Server Adaptor
#
class SocketServer(SocketPort):
  def __init__(self, reader, name, host, port):
    SocketPort.__init__(self, reader, name, host, port)
    self.socket = None
    self.service = []
    self.service_id = 0
    self.mainloop = False
    self.debug = False
    self.server_adaptor = None
    self.setServerMode()
    self.cometManager = CometManager(self)
    self.bind()

  #
  # 
  #
  def accept_service(self, flag=True):
    try:
      conn, addr = self.socket.accept()
      self.service_id += 1
      name = self.name+":service:%d" % self.service_id
      reader = copy.copy(self.reader)
      newadaptor = SocketService(self, reader, name, conn, addr)
      if flag :
        newadaptor.start()
      return newadaptor

    except:
#      print "ERROR in accept_service"
      pass

    return None

  def accept_service_loop(self, lno=5, timeout=1.0):
    print "Wait for accept: %s(%s:%d)" % (self.name, self.host, self.port)
    self.socket.listen(lno)
    while self.mainloop:
      res = self.wait_for_read(timeout) 
      if res == 1:
        self.accept_service()
      elif res == -1:
        self.terminate()
      else:
        pass
    
    print "Terminate all service %s(%s:%d)" % (self.name, self.host, self.port)
    self.close_service()
    self.close()
    return 

  #
  #
  #
  def getServer(self):
    return self

  #
  #
  #
  def run(self):
    self.accept_service_loop()

  #
  #
  #
  def remove_service(self, adaptor):
     try:
       self.service.remove(adaptor)
     except:
       pass

#
#  Service Adaptor
#
class SocketService(SocketPort):
  def __init__(self, server, reader, name, sock, addr):
    SocketPort.__init__(self, reader, name, addr[0], addr[1])
    self.socket = sock
    self.mainloop = False
    self.server_adaptor = server
    self.debug = False
    server.service.append(self)

  #
  #
  #
  def run(self):
    self.message_receiver()

  def getServer(self):
    return self.server_adaptor

#
#  Commands 
#
CloseCodeNum={
     'Normal':1000,
     'GoingAway':1001,
     'ProtocolError':1002,
     'UnsupportedData':1003,
     'Reserved':1004,
     'NoStatus':1005,
     'Abnormal':1006,
     'InvalidFrame':1007,
     'PolicyViolation':1008,
     'MessageTooBig':1009,
     'MandatoryExt.':1010,
     'InetranalError.':1011,
     'ServiceRestart.':1012,
     'TryAgain.':1013,
     'TLS_handshake.':1015,
}

Opcode={
     'ContinuationFrame.':0,
     'TextFrame.':1,
     'BinaryFrame.':2,
     'ConnectionCloseFrame.':8,
     'PingFrame.':9,
     'PongFrame.':10,
}

#
#  Foundmental reader class 
#
class CommReader:
  def __init__(self, owner=None, parser=None):
    self.buffer = ""
    self.bufsize = 0
    self.current=0
    self.response=""
    self.owner = owner
    if parser is None:
      self.parser = CommParser('')
    else:
      self.parser = parser
    self.debug = False

  #
  #  parse received data, called by SocketPort
  #
  def parse(self, data):
    if self.debug:
      print data
    self.appendBuffer( data )
    self.checkBuffer()

  #
  #  Usually 'owner' is a controller
  #
  def setOwner(self, owner):
    self.owner = owner

  def getServer(self):
    return  self.owner.getServer()

  #
  #  Buffer
  #
  def setBuffer(self, buffer):
    if self.buffer : del self.buffer
    self.buffer=buffer
    self.bufsize = len(buffer)
    self.current=0

  def appendBuffer(self, buffer):
    self.buffer += buffer
    self.bufsize = len(self.buffer)

  def skipBuffer(self, n=4, flag=1):
    self.current += n
    if flag :
      self.buffer = self.buffer[self.current:]
      self.current = 0
    return 

  def clearBuffer(self, n=0):
    if n > 0 :
      self.buffer = self.buffer[n:]
      self.current = 0
    else:
      if self.buffer : del self.buffer
      self.buffer = ""
      self.current = 0

  def checkBuffer(self):
    try:
      if len(self.buffer) > self.current :
        res = self.parser.checkMessage(self.buffer, self.current, self)
        if res == 0:
          return False
        self.buffer = self.buffer[res:]
        self.current = 0
    except:
      print "ERR in checkBuffer"
      self.buffer=""
      pass

    return False
     
  #
  # Send response message
  #
  def send(self, flag=False):
    if self.owner :
      self.owner.send(self.response)
    else:
      print "No owner"

    if flag:
      self.owner.close()
    return

  def sendResponse(self, res, flag=True):
    self.response = res
    self.send(flag)

  #
  # Append response message
  #
  def setResponse(self, msg):
    self.response += msg
    return

  #
  # Clear response message
  #
  def clearResponse(self):
    self.response=""
    return

  #
  #  extract data from self.buffer 
  #
  def read(self, nBytes, delFlag=1):
    start = self.current
    end = start + nBytes

    if self.bufsize < end :
      end = self.bufsize

    data = self.buffer[start:end]
    self.current = end

    if  delFlag :
      self.buffer =  self.buffer[end:]
      self.current =  0
    return data

  def getParser(self):
    return self.parser

#
#  Reader class for eSEAT port
#
class CometReader(CommReader):
  def __init__(self, rtc=None, dirname="html"):
    CommReader.__init__(self, None, HttpCommand(dirname))
    self.rtc = rtc
    self.dirname = dirname

  def getRtc(self):
    return self.rtc

  def doProcess(self, header, data):
    self.clearResponse()
    cmd = header["Http-Command"]
    fname = header["Http-FileName"]

    if cmd == "GET":
      contents = get_file_contents(fname, self.dirname)
      ctype = get_content_type(fname)

      if contents is None:
        response = self.parser.response404()
      else:
        response = self.parser.response200(ctype, contents)

      self.sendResponse(response)

    elif cmd == "POST":
      Data = parseData(data)

      if fname == "/comet_request" :
        self.cometRequest(Data)

      elif fname == "/comet_event" :
        self.cometTrigger(Data)

      else:
	  contents = "Hello, No such action defined"
          response = self.parser.response200("text/plain", contents)
          self.sendResponse(response)
    else:
      response = self.parser.response400()
      self.sendResponse(response)

    return

  def cometRequest(self, data):
    if data.has_key("id") :
      self.registerHandler(data)
    else:
      response = self.parser.response400()
      self.sendResponse(response)

  def cometTrigger(self, data):
     res = {}
     if data.has_key("id") :
       self.callHandler(data)
       res["result"] = "OK"
     else:
       res["result"] = "ERROR"

     res["date"] = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S JST")
     response = self.parser.response200("application/json", json.dumps(res))
     self.sendResponse(response)

  def registerHandler(self, data):
    server = self.getServer()
    server.cometManager.registerHandler(self, data['id'], data)
    return

  def callHandler(self, data):
    server = self.getServer()
    server.cometManager.callHandler(data['id'], data)
    return


#
# CommParser: parse the reveived message
#
class CommParser:
  def __init__(self, buffer, rdr=None):
    self.buffer=buffer
    self.bufsize = len(buffer)
    self.reader = rdr

    self.offset=0
    self.cmdsize = 0

    self.encbuf=None
    self.encpos=0

  #
  #  for buffer
  #
  def setBuffer(self, buffer):
    if self.buffer : del self.buffer
    self.buffer=buffer
    self.bufsize = len(buffer)
    self.offset=0

  def clearBuffer(self):
    self.setBuffer("")

  def appendBuffer(self, buffer):
    self.buffer += buffer
    self.bufsize = len(self.buffer)

  #
  #  skip buffer, but not implemented....
  #
  def skipBuffer(self):
      print "call skipBuffer"
      return 
  #
  #  check message format (cmd encoded_args)
  #
  def checkMessage(self, buffer, offset=0, reader=None):
    return None

#
#  Httpd  
#     CommParser <--- HttpCommand
#
class HttpCommand(CommParser):
  def __init__(self, dirname=".", buffer=''):
    CommParser.__init__(self, buffer)
    self.dirname=dirname
    self.buffer = buffer

  def setRootDir(self, dirname):
    self.dirname=dirname

  #
  #
  #
  def checkMessage(self, buffer, offset=0, reader=None):
    pos = self.parseHttpdHeader( buffer, offset)
    if pos > 0 :
      reader.doProcess(self.header, self.data)
      return pos
    return 0

  #
  #
  #
  def parseHttpdHeader(self, buffer, offset=0):
    self.header = {}
    self.data = ""

    pos =  buffer[offset:].find("\r\n\r\n")

    if pos > 0:
      pos += offset + 4
      self.headerMsg = buffer[offset:pos]
      self.buffer = buffer[pos:]

      header = self.headerMsg.split("\r\n")
      cmds = header[0].split(' ')
      cmd = cmds[0].strip()
      fname = cmds[1].strip()
      if fname == "/" : fname = "/index.html"
      proto = cmds[2].strip()

      header.remove( header[0] )
      self.header = self.parseHeader(header)
      self.header["Http-Command"] = cmd
      self.header["Http-FileName"] = fname
      self.header["Http-Proto"] = proto

      if self.header.has_key("Content-Length") :
        contentLen = int(self.header["Content-Length"])
	pos += contentLen
        self.data = self.buffer[:contentLen]

      return pos
    return 0

  #
  #  parse HTTP Header
  #
  def parseHeader(self, header):
    res = {}
    for h in header:
      if h.find(":") > 0 :
        key, val = h.split(':', 1)
        res[key.strip()] = val.strip()
    return res

  #
  # Generate response message
  #
  def response200(self, ctype, contents):
    date = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S JST")
    res  = "HTTP/1.0 200 OK\r\n"
    res += "Date: "+date+"\r\n"
    res += "Content-Type: "+ctype+"\r\n"
    res += "Content-Length: "+str(len(contents))+"\r\n"
    res += "\r\n"
    res += contents

    return res

  def response404(self):
    date = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S JST")
    res  = "HTTP/1.0 404 Not Found\r\n"
    res += "Date: "+date+"\r\n"
    res += "\r\n"
    return res

  def response400(self):
    date = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S JST")
    res  = "HTTP/1.0 400 Bad Request\r\n"
    res += "Date: "+date+"\r\n"
    res += "\r\n"
    return res

#
#     CometManager
#
class CometManager:
  def __init__(self, server):
    self.server = server
    self.long_pollings = {}

  def resieter(self, reader, id):
    self.long_pollings[id] = reader

  def registerHandler(self, reader, id, data):
    self.long_pollings[id] = reader
    return

  def callHandler(self, id, data):
    res = {}
    res['date'] = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S JST")
    res['message'] = "Push message"

    if id == "all":
      self.response_all(res, "application/json")
    else:
      self.response(id, res, "application/json")
    return

  def response(self, id, json_data, ctype="text/plain"):
    reader = self.long_pollings[id]
    if reader :
      json_data['id'] = id
      try :
        json_data['result'] = reader.rtc.onComet()
      except:
	json_data['result'] = ""

      contents = json.dumps(json_data)
      responsemsg = reader.parser.response200(ctype, contents)
      reader.sendResponse(responsemsg)
      self.long_pollings[id] = None

  def response_all(self, json_data, ctype="text/plain"):
    keys = self.long_pollings.keys()
    for k in  keys :
      self.response(k, json_data, ctype)

############# Functoins
#
#
#
def get_file_contents(fname, dirname="."):
  contents = None
  try:
    f=open(dirname+fname,'rb')
    contents = f.read()
    f.close()
  except:
    pass
  return contents

#
#
#
def get_content_type(fname):
  imgext=["jpeg", "gif", "png", "bmp"]
  htmext=["htm", "html"]
  ctype = "text/plain"
  ext=fname.split(".")[-1]
  if htmext.count(ext) > 0:
    ctype = "text/html"
  elif ext == "txt" :
    ctype = "text/plain"
  elif ext == "css" :
    ctype = "text/css"
  elif ext == "js" :
    ctype = "text/javascript"
  elif ext == "csv" :
    ctype = "text/csv"
  elif ext == "jpg" :
    ctype = "image/jpeg"
  elif imgext.count(ext) > 0:
    ctype = "image/"+ext
  else:
    pass
  return ctype

def parseData(data):
  res = {}
  ar = data.split("&")
  for a in ar:
    key, val = a.split("=")
    res[key.strip()] = val.strip()
  return res
#
#
#
def create_httpd(num=80, top="html"):
  return SocketServer(CometReader(None), "Web", "localhost", num)
