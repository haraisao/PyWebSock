#
#
import threading
import time

class FuncTest(threading.Thread):
  def __init__(self, f):
    threading.Thread.__init__(self)
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
    self.sq=syncQueue()

  def minus2(self, v):
    return v-2

  def super(self):
    return super(Func2, self)

  def put(self, val):
    self.sq.put(val)
    return

  def run(self):
    val=self.sq.get()
    for i in range(3):
      print "count %s[%d]" %( val, i)
      time.sleep(1)
    return 

class syncQueue:
    def __init__(self):
        self.cv = threading.Condition()
        self.queue = []

    def put(self, item):
        with self.cv:
            self.queue.append(item)
            self.cv.notifyAll()

    def get(self):
        with self.cv:
            while not len(self.queue) > 0:
                self.cv.wait()
            return self.queue.pop(0)

class adminId():
  def __init__(self, n=10):
    self.seq_queue=[]
    self.sq=[]
    self.released=[]
    self.next_id=0
    for i in range(n):
      self.sq.append( syncQueue() )
      if i < n-1:
        self.seq_queue.append(i+1)
      else:
        self.seq_queue.append(-1)
        self.last_id=i

  def request(self):
    if self.seq_queue[self.next_id] == -1: return None
    res = self.next_id
    self.next_id = self.seq_queue[self.next_id]
    self.seq_queue[res] = -1
    return res

  def release(self,val):
    if self.last_id == val: return
    if self.seq_queue[val] == -1:
      self.seq_queue[self.last_id] = val
      self.last_id = val
#      print "Release %d" % val
    else:
      print "Error in Release[%d]" % val
    return
