import time
import socket
import sys
import os
import random
import threading


if len(sys.argv)<6:
    print("Please provide all the required argument as <server-IP> server-port# file-name N MSS ")
    raise SystemExit

serverIP=str(sys.argv[1])
serverport=int(sys.argv[2])
filetobesent=str(sys.argv[3])
WinSize=int(sys.argv[4])
MSS=int(sys.argv[5])

UDPsock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ClientSP=random.randint(1025,60000)
client=('', ClientSP)
server=(serverIP,serverport)

try:
    UDPsock.bind(client)
    print("client Started listening on", client)
    UDPsock.settimeout(0.1)
    print("Timeout value is set to 0.1 seconds")
except socket.error:
    print("Port already used, Please try again")
    raise SystemExit

packet=[]
fileSize=os.path.getsize(filetobesent)
with open(filetobesent,"rb") as f:
    data=f.read()
    f.close()

start=0
end=MSS
while fileSize>=0:
    if fileSize < MSS:
        end=start+fileSize
    if start==end:
        break
    packet.append(data[start:end])
    start+=MSS
    end+=MSS
    fileSize-=MSS

def checksum(segment, length):
    if (length % 2 != 0):
        segment += "0".encode('utf-8')
    x = segment[0] + ((segment[1]) << 8)
    y = (x & 0xffff) + (x >> 16)

    for i in range(2, len(segment), 2):
        x = segment[i] + ((segment[i + 1]) << 8)
        y = ((x + y) & 0xffff) + ((x + y) >> 16)
    return '{:16b}'.format(~y & 0xffff)

pktidentifier='0101010101010101'
buffer=WinSize
sqnNum=0
startfunc=1



def rdt_send(UDPsock):
    global buffer,sqnNum,startfunc
    print("Starting the file transfer")
    
    while startfunc:
        while buffer > 0 and sqnNum < len(packet):
            sqnSent='{:032b}'.format(sqnNum)
            checksumSent=checksum(packet[sqnNum],len(packet[sqnNum]))
            packetent=sqnSent.encode('utf-8')+checksumSent.encode('utf-8')+pktidentifier.encode('utf-8')+packet[sqnNum]
            sqnNum = (sqnNum+1)%(2**31-1)
            buffer-=1
            UDPsock.sendto(packetent, server)

def ack_recv(conn):
    global buffer,sqnNum,startfunc
    checkSqn=0
    startTime=time.time()
    while startfunc:
        try:
            Acknum=conn.recv(1024)
            Acknum=Acknum.decode('utf-8')
            if Acknum[0:32]=='{:032b}'.format(checkSqn):
                buffer+=1
                checkSqn+=1
        except socket.timeout:
            print("Timeout, sequence number = ",checkSqn)
            buffer=WinSize
            sqnNum=checkSqn
        if checkSqn==len(packet):
            UDPsock.sendto("Bye".encode('utf-8'), server)
            UDPsock.close()
            print("The file has been successfully transferred")
            endTime=time.time()
            RTT= endTime - startTime
            print('Total delay for transferring the sendfile is : ' + str('{0:02f}'.format(RTT)) + ' seconds')
            startfunc=0

sendThread=threading.Thread(target=rdt_send, args=(UDPsock,))
ackThread=threading.Thread(target=ack_recv, args=(UDPsock,))
sendThread.start()
ackThread.start()
sendThread.join(timeout=0.5)
ackThread.join(timeout=0.5)