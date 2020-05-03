import shlex
from socket import *
import sys
import struct
import json
import time
import zlib
import random
import string
def _nZ(n):
    return n if n != 0 else 1e-6
def randomString(stringLength=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

def _bA(a,b):
    return bytes("".join([a,b]))
class Filter(object):
    def __init__(self):
        super(Filter, self).__init__()
    def Encode(self,data):
        return bytes(data)
    def Decode(self,data):
        return bytes(data)
SIGNATURE     = 0x4B1DC0DE
BUFFER        = 4096
PACKET_LENGTH = 8 
class TEOPSClient(object):
    Sended         = 0
    Received       = 0
    PACKET_LENGTH  = PACKET_LENGTH
    SIGNATURE      = SIGNATURE
    BUFFER         = BUFFER
    def __init__(self,client,Filter):
        super(TEOPSClient, self).__init__()
        self.client=client
        self.Filter = Filter
    def SendBlock(self,block_string):
        encoded = self.Filter.Encode(block_string)
        length = len(encoded)
        meta = struct.pack("!II",self.SIGNATURE,length)
        buffer = bytes("".join([
            meta,
            encoded
        ]))
        self.client.send(buffer)
        self.Sended = length+self.PACKET_LENGTH
        return length+self.PACKET_LENGTH
    def ReceiveBlock(self):
        try:
            meta = struct.unpack("!II",self.client.recv(self.PACKET_LENGTH))
        except struct.error:
            return None
        if(meta[0] != self.SIGNATURE):
            return
        else:
            remaining = meta[1]
            buffer = b""
            while remaining != 0:
                need = self.BUFFER if remaining >= self.BUFFER else remaining
                tmp = self.client.recv(need)
                self.Received+=need
                buffer = _bA(buffer,tmp)
                remaining = remaining-need
            decoded = self.Filter.Decode(buffer)
            return decoded
    def _bA(self,a,b):
        return bytes("".join([a,b]))
    def SendDict(self,dct={}):
        return self.SendBlock(json.dumps(dct))
    def ReceiveDict(self):
        return json.loads(self.ReceiveBlock())
class TEOPS(socket):
    Sended         = 0
    Received       = 0
    PACKET_LENGTH  = PACKET_LENGTH
    SIGNATURE      = SIGNATURE
    BUFFER         = BUFFER
    LISTEN         = 5
    Connections={}
    def __init__(self, family=AF_INET, type=SOCK_STREAM, proto=0, _sock=None,Filter=Filter()):
        super(TEOPS, self).__init__(family=family, type=type, proto=proto, _sock=_sock)
        self.Filter=Filter
    def BindServer(self,host):
        r = self.bind(host)
        self.listen(self.LISTEN)
        return r
    def ConnectServer(self,host):
        return self.connect(host)
    def AcceptClient(self):
        conn,addr = self.accept()
        conn_ = TEOPSClient(conn,self.Filter)
        self.Connections[addr] = conn_
        return (conn_,addr)
    def SendBlock(self,block_string):
        encoded = self.Filter.Encode(block_string)
        length = len(encoded)
        meta = struct.pack("!II",self.SIGNATURE,length)
        buffer = bytes("".join([
            meta,
            encoded
        ]))
        self.send(buffer)
        self.Sended = length+self.PACKET_LENGTH
        return length+self.PACKET_LENGTH
    def ReceiveBlock(self):
        try:
            meta = struct.unpack("!II",self.recv(self.PACKET_LENGTH))
        except struct.error:
            return None
        if(meta[0] != self.SIGNATURE):
            return
        else:
            remaining = meta[1]
            buffer = b""
            while remaining != 0:
                need = self.BUFFER if remaining >= self.BUFFER else remaining
                tmp = self.recv(need)
                self.Received+=need
                buffer = _bA(buffer,tmp)
                remaining = remaining-need
            decoded = self.Filter.Decode(buffer)
            return decoded
    def SendDict(self,dct={}):
        return self.SendBlock(json.dumps(dct))
    def ReceiveDict(self):
        return json.loads(self.ReceiveBlock())
class CompressFilter(Filter):
    def __init__(self):
        super(CompressFilter, self).__init__()
    def Encode(self,data):
        return zlib.compress(data)
    def Decode(self,data):
        return zlib.decompress(data)
from base64 import b64encode,b64decode
class Base64Filter(Filter):
    def __init__(self):
        super(Base64Filter, self).__init__()
    def Encode(self,data):
        return b64encode(data)
    def Decode(self,data):
        return b64decode(data)
def test_server(host):
    host = (
        host[0].replace("*","0.0.0.0"),
        int(host[1].replace("*","29791"))
        )
    print("Binding via TEOPS %s:%s..."%host)
    server = TEOPS(Filter=Base64Filter())
    server.BindServer(host)
    print("Binded.")
    conn,ip = server.AcceptClient()
    print("Dict test")
    Done = False
    while not Done:
        clientdict = conn.ReceiveDict()
        print("Message: %(message)s Iteration: %(iteration)s Timestamp: %(timestamp)s"%clientdict)
        Done = clientdict["done"]

    print("Total Received: %s KB "%(conn.Received))
    print("Bandwidth test")
    
    received = 0
    Done = False
    cz = 1024*32
    cb = 0
    rp = 128*1024
    stime = time.time()
    max_ = 0
    while not Done:
        block = conn.ReceiveBlock()
        if not block:
            Done = True
            break
        cb+=4096
        length = len(block)
        received+=length
        if(received%rp == 0 and received>0):
            etime=time.time()
            speed = rp/(1024*(etime-stime))
            sys.stdout.write("Received : %.4f MB Speed : %.2f KB/s        \r"%(
                received/(1024.**2),
                speed
                )
            )
            if(max_<speed):
                max_=speed
            stime=time.time()
    print("\n")
    print("Max speed Download : %.4f KB/s"%(max_))
    print("Total Received: %.4f MB "%(conn.Received/1024.**2))
def test_client(host):
    host = (
        host[0].replace("*","0.0.0.0"),
        int(host[1].replace("*","29791"))
        )
    print("Connecting via TEOPS %s:%s..."%host)
    client = TEOPS(Filter=Base64Filter())
    client.ConnectServer(host)
    print("Connected.")
    print("Dict Test")
    for i in range(0,32):
        client.SendDict({
            "message":"hello %s"%(randomString(6)),
            "iteration":i,
            "timestamp":time.time(),
            "done":False
        })
    client.SendDict({
            "message":"hello %s"%(randomString(6)),
            "iteration":0,
            "timestamp":time.time(),
            "done":True
        })
    print("Bandwidth test")
    datasize = 10*1024**2 # 100 MB
    sended = 0
    remaining = datasize
    cz = 1024*32
    cb = 0
    rp = 512*1024
    stime = time.time()
    while remaining != 0:
        client.SendBlock(randomString(4096))
        cb+=4096
        speed = sended/(1024*(time.time()-stime))
        if(sended%rp == 0):
            sys.stdout.write("Sended : %.4f MB Speed: %.2f KB/s         \r"%(
                rp/(1024.**2),
                speed
                )
            )
        sended += 4096
        remaining-=4096
    client.close()
def main(args):
    if(len(args)==2):
        return test_server(tuple(args[1].split(":"))) if args[0] == "server" else test_client(tuple(args[1].split(":")))

if __name__ == "__main__":
    main(shlex.split(" ".join(sys.argv))[1:])