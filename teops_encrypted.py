import shlex
import sys
import pyaes
import time
import string
import random
from teops import TEOPS,TEOPSClient,Filter

def randomString(stringLength=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))
class AESFilter(Filter):
    def __init__(self,
    key="\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"):
        super(AESFilter, self).__init__()
        self.key = key
        self.AESEncryptor = pyaes.AESModeOfOperationCTR(self.key)
        self.AESDecryptor = pyaes.AESModeOfOperationCTR(self.key)
    def Encode(self,data):
        return self.AESDecryptor.encrypt(data)
    def Decode(self,data):
        return self.AESDecryptor.decrypt(data)
KEY = "\xDE\xAD\xBA\xAD\xDE\xAD\xBA\xAD\xDE\xAD\xBA\xAD\xDE\xAD\xBA\xAD\xDE\xAD\xBA\xAD\xDE\xAD\xBA\xAD\xDE\xAD\xBA\xAD\xDE\xAD\xBA\xAD"
def test_server(host):
    host = (
        host[0].replace("*","0.0.0.0"),
        int(host[1].replace("*","29791"))
        )
    print("Binding via TEOPS %s:%s..."%host)
    Encryptor = AESFilter(KEY)
    server = TEOPS(Filter=Encryptor)
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
            sys.stdout.write("Received : %.4f MB Speed : %.2f KB/s F:%s       \r"%(
                received/(1024.**2),
                speed,
                block[0:8]
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
    Encryptor = AESFilter(KEY)
    client = TEOPS(Filter=Encryptor)
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
    datasize = 3*1024**2 # 100 MB
    sended = 0
    remaining = datasize
    cz = 1024*32
    cb = 0
    rp = 512*1024
    stime = time.time()
    data = "DEADBEEF"*512
    while remaining != 0:
        client.SendBlock(data)
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