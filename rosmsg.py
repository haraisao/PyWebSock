#
#
import sys
import os
import re

MSG_EXT=".msg"

primitive_type=["bool", "int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float32", "float64", "string", "time", "duration"]

header_type=["Header"]

#
#
#
def load_msg_file(typename, pkg_name="", ext=MSG_EXT):
  try:
    path=""
    if pkg_name:
      pathes = pkg_name.split('/')
      for p in pathes:
        path += p+"/msg/"
    filename = path+typename+ext

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
        typ = parse_datatype(typ.strip(), pkg_name)

        data[name.strip()] = typ
    return data
  except:
    print "ERROR in load_msg_file (%s %s)" % (typename, pkg_name)

#
#
#
def parse_datatype(typ, pkg_name="", ext=MSG_EXT):
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


