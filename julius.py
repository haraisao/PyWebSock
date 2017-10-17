#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Julius speech recognition component

Copyright (C) 2010
    Yosuke Matsusaka
    Intelligent Systems Research Institute,
    National Institute of Advanced Industrial Science and Technology (AIST),
    Japan
    All rights reserved.

Copyright (C) 2017
    Isao Hara
    National Institute of Advanced Industrial Science and Technology (AIST),
    Japan
    All rights reserved.

Licensed under the Eclipse Public License -v 1.0 (EPL)
http://www.opensource.org/licenses/eclipse-1.0.txt
'''

import sys, os, socket, subprocess, signal, threading, platform
import time, struct, traceback, locale, codecs, getopt, wave, tempfile
import optparse
from glob import glob
#from BeautifulSoup import BeautifulSoup
from lxml import *
from bs4 import BeautifulSoup
from xml.dom.minidom import Document

import ConfigParser

'''
Dictation-kit
main.jconf:
  -d model/lang_m/bccwj.60k.bingram  # 単語2-gram,3-gramファイル(バイナリ形式）
  -v model/lang_m/bccwj.60k.htkdic   # 単語辞書ファイル
  -b 1500                            # 第1パスのビーム幅（ノード数
  -b2 100                            # 第2パスの仮説数ビームの幅（仮説数）
  -s 500                             # 第2パスの最大スタック数 (仮説数)
  -m 10000                           # 第2パスの仮説オーバフローのしきい値
  -n 30                              # 第2パスで見つける文の数（文数）
  -output 1                          # 第2パスで見つかった文のうち出力する数 （文数）
  -zmeanframe                        # フレーム単位のDC成分除去を行う (HTKと同処理)
  -rejectshort 800                   # 指定ミリ秒以下の長さの入力を棄却する
  
am-gmm.jconf
  -h model/phone_m/jnas-tri-3k16-gid.binhmm    # 音響HMM定義ファイル
  -hlist model/phone_m/logicalTri-3k16-gid.bin # 論理的に出現しうる triphone -> 定義されている triphoneの対応を指定した「HMMListファイル」
  -lmp  10 0  # 言語重みと挿入ペナルティ: 第1パス(2-gram)
  -lmp2 10 0  # 言語重みと挿入ペナルティ: 第2パス(3-gram)


'''

#
#  Julius Wrappper
#
class JuliusWrap(threading.Thread):
    CB_DOCUMENT = 1
    CB_LOGWAVE = 2
    
    #
    #  Constructor
    #
    def __init__(self, language='jp', rtc=''):
        threading.Thread.__init__(self)
        self._running = False
        self._platform = platform.system()
        self._gotinput = False
        self._lang = language
        self._memsize = "large"
        #self._memsize = "medium"

        self._logdir = tempfile.mkdtemp()
        self._callbacks = []
        self._grammars = {}
        self._firstgrammar = True
        self._activegrammars = {}
        self._prevdata = ''

        self._jconf_file = ""

        #self._mode = 'grammar'
        self._mode = 'dictation'

        self._jcode = 'utf-8'

        self._silence = getWavData('silence.wav')

        self._modulesocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._audiosocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._audiohost = "localhost"
        self._audioport = 0
        self._modulehost = "localhost"
        self._moduleport = 0

        self.loadConfigFile()

    def loadConfigFile(self, fname="Julius.ini"):
        self._config = ConfigParser.SafeConfigParser()
        self._config.read(fname)

        self._julius_runkitdir = self._config.get('Julius', 'basedir')
        self._basedir = './'

        self._julius_bin=os.path.join(self._julius_runkitdir, "bin", "windows", "julius.exe")

        self._julius_hmm_ja   = os.path.join(self._julius_runkitdir, "model", "phone_m", "jnas-tri-3k16-gid.binhmm")
        self._julius_hlist_ja = os.path.join(self._julius_runkitdir, "model", "phone_m", "logicalTri-3k16-gid.bin")
        self._julius_ngram_ja = os.path.join(self._julius_runkitdir, "model", "lang_m", "bccwj.60k.bingram")
        self._julius_dict_ja  = os.path.join(self._julius_runkitdir, "model", "lang_m", "bccwj.60k.htkdic")
        #
        # for dictation
        self._julius_bingram_ja= os.path.join(self._julius_runkitdir, "model", "lang_m", "bccwj.60k.bingram")
        self._julius_htkdic_ja = os.path.join(self._julius_runkitdir, "model", "lang_m", "bccwj.60k.htkdic")


    def startJulius(self):
        ###########################################################

        if self._mode != 'client' :
            self.setupSubprocess()

            print "command line: %s" % " ".join(self._cmdline)
            print self._cmdline
            self._p = subprocess.Popen(self._cmdline)

            self._running = True


        #####################################################
        #
        #   Connect to Julius (try ten times)
        time.sleep(1)
        print "connecting to ports"
        for retry in range(0, 10):
            try:
                self._modulesocket.connect((self._modulehost, self._moduleport))
            except socket.error:
                time.sleep(1)
                continue
            break
        for retry in range(0, 10):
            try:
                self._audiosocket.connect(( self._audiohost, self._audioport))
            except socket.error:
                time.sleep(1)
                continue
            break

        #
        # for grammar mode
        if self._mode == 'grammar' :
            self._modulesocket.sendall("INPUTONCHANGE TERMINATE\n")

        self._running = True

        print "JuliusWrap started"

    #
    def setJuliusServer(self, host, mport, aport):
       self._mode = 'client'
       self._audiohost = host
       self._audioport = aport
       self._modulehost = host
       self._moduleport = mport
    #
    # Parameter seting for Julius
    #
    def setupSubprocess(self):
        self._cmdline = []
        self._cmdline.append(self._julius_bin)

        if self._mode == 'dictation' :
            # dictation-kit-v4.4(GMM版デフォルトパラメータ）ただし、outputを5に変更
            self._cmdline.extend(['-d',     self._julius_bingram_ja])
            self._cmdline.extend(['-v',     self._julius_htkdic_ja])
            self._cmdline.extend(['-h',     self._julius_hmm_ja])
            self._cmdline.extend(['-hlist', self._julius_hlist_ja])
            self._cmdline.extend(["-b", "1500", "-b2", "100", "-s", "500" ,"-m", "10000"])
            self._cmdline.extend(["-n", "30", "-output", "5", "-zmeanframe", "-rejectshort" ,"800", "-lmp", '10' ,'0', '-lmp2', '10', '0'])
        else:
            #
            #  Japanese
            if self._lang in ('ja', 'jp'):
                self._cmdline.extend(['-h',  self._julius_hmm_ja])
                self._cmdline.extend(['-hlist', self._julius_hlist_ja])
                self._cmdline.extend(["-dfa", os.path.join(self._basedir, "dummy.dfa")])
                self._cmdline.extend(["-v" , os.path.join(self._basedir, "dummy.dict")])
                self._cmdline.extend(["-sb", "80.0"])

            #
            #  English
            else:
                self._cmdline.extend(['-h',  self._julius_hmm_en])
                self._cmdline.extend(['-hlist', self._julius_hlist_en])
                self._cmdline.extend(["-dfa", os.path.join(self._basedir, "dummy-en.dfa")])
                self._cmdline.extend(["-v", os.path.join(self._basedir, "dummy-en.dict")])
                self._cmdline.extend(["-sb", "160.0"])
    
            #
            #  large model or small model
            #
            if self._memsize == "large":
                self._cmdline.extend(["-b", "-1", "-b2", "120", "-s", "1000" ,"-m", "2000"])
            else:
                self._cmdline.extend(["-b", "-1", "-b2", "80", "-s", "500" ,"-m", "1000"])
    
            self._cmdline.extend(["-n", "5", "-output", "5"])
            self._cmdline.extend(["-rejectshort", "200"])
            self._cmdline.extend(["-penalty1", "5.0", "-penalty2", "20.0"]) # (文法使用時) 第1,2パス用の単語挿入ペナルティ

        self._cmdline.extend(["-pausesegment"])         # レベル・零交差による音声区間検出の強制ON
        self._cmdline.extend(["-nostrip"])              # ゼロ続きの無効な入力部の除去をOFFにする
        self._cmdline.extend(["-spmodel", "sp"])        # ショートポーズ音響モデルの名前
        self._cmdline.extend(["-iwcd1", "max"])         # 第1パスの単語間トライフォン計算法を指定する．(同じコンテキストのトライフォン集合の全尤度の最大値を近似尤度として用いる)
        self._cmdline.extend(["-gprune", "safe"])       # safe pruning 上位N個が確実に求まる．正確．
        self._cmdline.extend(["-forcedict"])            # エラー単語を無視して続行する
        self._cmdline.extend(["-record", self._logdir]) # 認識した音声データを連続したファイルに自動保存
        self._cmdline.extend(["-smpFreq", "16000"])     # サンプリング周波数(Hz)

        self._audioport = self.getunusedport()
        self._cmdline.extend(["-input", "adinnet",  "-adport",  str(self._audioport)]) # 入力の設定（adinport使用)

        if self._jconf_file :
            self._cmdline.extend(["-C", self._jconf_file]) # overwrite parameters by jconf file.

        self._moduleport = self.getunusedport()
        self._cmdline.extend(["-module", str(self._moduleport)])                       # module mode


    #
    #  Connect to Julius
    def connect_to_julius(self, host, port):
        if not self._modulesocket :
            self._modulesocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._modulesocket.connect((host, port))
            self._modulehost = host
            self._moduleport = port
            return Ture
        except socket.error:
            return False

    #
    #  close Julius
    def close_julius(self):
        if self._modulesocket :
            self._modulesocket.shutdown(socket.SHUT_RDWR)
            self._modulesocket.close()
            self._modulesocket = None

    #
    #  Connect to Adinnet
    def connect_to_adinnet(self, host, port):
        if not self._audiosocket :
            self._audiosocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._audiosocket.connect((host, port))
            self._audiohost = host
            self._audioport = port
            return True
        except socket.error:
            return False

    #
    #  close Adinnet
    def close_adinnet(self):
        if self._audiosocket :
            self._audiosocket.shutdown(socket.SHUT_RDWR)
            self._audiosocket.close()
            self._audiosocket = None


    #
    #  get unused communication port
    #
    def getunusedport(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('localhost', 0))
        addr, port = s.getsockname()
        s.close()
        return port

    #
    #  Terminate (Call on Finished)
    #
    def terminate(self):
        print 'JuliusWrap: terminate'
        self._running = False
        self.close_adinnet()
        self.close_julius()

        self._p.terminate()
        return 0

    #
    #
    def flush(self):
        self.write(self._silence)
    #
    #
    def loadWav(self, fname):
        data=getWavData(fname)
        data += self._silence
        self.write(data)

    #
    #   Write to audio data
    #
    def write(self, data):
        try:
            self._audiosocket.send(struct.pack("i", len(data)))
            self._audiosocket.sendall(data)
        except socket.error:
            try:
                self._audiosocket.connect((_audiohost, self._audioport))
            except:
                pass
        return 0

    #
    #  Run
    #
    def run(self):
        while self._running:
            #for f in glob(os.path.join(self._logdir, "*.wav")):
            #    for c in self._callbacks:
            #        c(self.CB_LOGWAVE, f)
            try:
                self._modulesocket.settimeout(1)
                data = self._prevdata + unicode(self._modulesocket.recv(1024*10),  self._jcode)

            except socket.timeout:
                continue
            except socket.error:
                print 'socket error'
                break
            print data
            self._gotinput = True
            ds = data.split(".\n")
            self._prevdata = ds[-1]
            ds = ds[0:-1]
            for d in ds:
                try:
                  dx = BeautifulSoup(d, "lxml")
                  for c in self._callbacks:
                      c(self.CB_DOCUMENT, dx)
                except:
                  import traceback
                  traceback.print_exc()
                  pass

        print 'JuliusWrap: exit from event loop'

    #
    #   Add grammer to Julius Server
    #
    def addgrammar(self, data, name):
        if self._firstgrammar == True:
            self._modulesocket.sendall("CHANGEGRAM %s\n" % (name,))
            self._firstgrammar = False
        else:
            self._modulesocket.sendall("ADDGRAM %s\n" % (name,))
        self._modulesocket.sendall(data.encode(self._jcode, 'backslashreplace'))
        self._grammars[name] = len(self._grammars)
        self._activegrammars[name] = True
        time.sleep(0.1)

    #
    #  Activate current grammer
    #
    def activategrammar(self, name):
        try:
            gid = self._grammars[name]
        except KeyError:
            print "[error] unknown grammar: %s" % (name,)
            return
        print "ACTIVATEGRAM %s" % (name,)
        self._modulesocket.sendall("ACTIVATEGRAM\n%s\n" % (name,))
        self._activegrammars[name] = True
        time.sleep(0.1)

    #
    #  Deactivate current grammer
    #
    def deactivategrammar(self, name):
        try:
            gid = self._grammars[name]
        except KeyError:
            print "[error] unknown grammar: %s" % (name,)
            return
        print "DEACTIVATEGRAM %s" % (name,)
        self._modulesocket.sendall("DEACTIVATEGRAM\n%s\n" % (name,))
        del self._activegrammars[name]
        time.sleep(0.1)

    #
    #  Synchronize grammer
    #
    def syncgrammar(self):
        self._modulesocket.sendall("SYNCGRAM\n")

    #
    #  Switch grammer
    #
    def switchgrammar(self, name):
        self.activategrammar(name)
        for g in self._activegrammars.keys():
            if g != name:
                self.deactivategrammar(g)

    #
    #  Set callback function
    #
    def setcallback(self, func):
        self._callbacks.append(func)

def getWavData(fname):
    try:
        f = wave.open(fname)
        data = f.readframes(f.getnframes())
        f.close()
        return data
    except:
        return ""
