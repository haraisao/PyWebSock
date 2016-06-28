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
    
class Func2(FuncTest):
  def __init__(self, f):
    FuncTest.__init__(self,f)

  def minus2(self, v):
    return v-2

