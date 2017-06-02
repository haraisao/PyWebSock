#
#
import sys
import os
import re

MSG_EXT=".msg"

primitive_type=["bool", "int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float32", "float64", "string", "time", "duration"]

header_type=["Header"]

MSG_PATH=["", "../common_msgs-jade-devel/"]

#
#
#
def parse_msg_type(typename):
  types = typename.split("/")
  if len(types) == 1:
    return load_msg_file(typename)

  return load_msg_file(types[1], types[0])

#
#
#
def load_msg_file(typename, pkg_name="", ext=MSG_EXT):
  try:
    filename = find_msg_file(typename, pkg_name)

    if not filename:
      print "ERROR: no such type.."
      return None

    f = open(filename, "r")
    lines = f.readlines()
    f.close()
    data={}
    for line in lines:
      ln = line.split("#", 2)
      if len(ln) == 1 or (len(ln) == 2 and ln[0]):
        ll = ln[0].strip()
        if not ll: continue
        typ, name = ll.split()
        typ = check_datatype(typ.strip(), pkg_name)

        data[name.strip()] = typ
    return data
  except:
    print "ERROR in load_msg_file (%s %s)" % (typename, pkg_name)
    return None

#
#
#
def check_datatype(typ, pkg_name="", ext=MSG_EXT):
  try:
    if typ in primitive_type or typ in header_type:
      return typ

    for p in primitive_type:
      m = re.search(p+"\[\d*\]", typ)
      if m : return typ

    data = load_msg_file(typ, pkg_name)
    return data

  except:
    print "ERROR in parse_datatype"
    return None

#
#
def find_msg_file(typename, pkg_name="", ext=MSG_EXT):
  try:
    path=""
    if pkg_name:
      path += pkg_name+"/msg/"

    for p in MSG_PATH:
      filename = p+path+typename+ext
      if os.path.exists(filename) :
        return filename

    return None

  except:
    print "ERROR in parse_datatype"
    return None

#
# Message Class
#
class ROS_Message:
  def __init__(self, name):
    self.name = name
    self.msg_type = parse_msg_type(name)


