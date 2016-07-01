#
#
class FuncTest():
  def __init__(self, f):
    self.func = f

  def plus1(self, v):
    return v+1

  def minus1(self, v):
    return v-1

  def call(self, f, args):
    if f in FuncTest.__dict__:
      mth = FuncTest.__dict__[f]
      return mth(self, args)
    else:
      print "No such method"

  def callfunc(self, args):
    if self.func in FuncTest.__dict__:
      mth = FuncTest.__dict__[self.func]
      return mth(self, args)
    else:
      print "No such method %s" % self.func
#
#    
class Func2(FuncTest):
  def __init__(self, f):
    FuncTest.__init__(self,f)

  def minus2(self, v):
    return v-2

  def super(self):
    return super(Func2, self)


class adminId():
  def __init__(self):
    self.queue=[1,2,3,4,5,6,7,8,9,-1]
    self.released=[]
    self.next_id=0
    self.last_id=9

  def request(self):
    if self.queue[self.next_id] == -1: return None
    res = self.next_id
    self.next_id = self.queue[self.next_id]
    self.queue[res] = -1
    return res

  def release(self,val):
    if self.last_id == val: return
    if self.queue[val] == -1:
      self.queue[self.last_id] = val
      self.last_id = val
      print "Release %d" % val
    else:
      print "Error"
    return
