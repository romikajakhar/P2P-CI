import random
import sys
import socket


if len(sys.argv)<3:
    print("Wrong Input")
    raise SystemExit

fileName=sys.argv[1]
LossProb=float(sys.argv[2])
if LossProb >=1 or LossProb <=0:
    print("p must be between 0 and 1")
    raise SystemExit

server=('', 7735)
serverUDPsock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverUDPsock.bind(server)
print("Server started listening on port 7735, Waiting for the client to connect ...")

def checksum(segment, length):
    if (length % 2 != 0):
        segment += "0".encode('utf-8')

    x = segment[0] + ((segment[1]) << 8)
    y = (x & 0xffff) + (x >> 16)

    for i in range(2, len(segment), 2):
        x = segment[i] + ((segment[i + 1]) << 8)
        y = ((x + y) & 0xffff) + ((x + y) >> 16)
    return ~y & 0xffff

expectedsqn=0
ackidentifier=43690
zeropad=0
f=open(fileName, 'a+')

while True:
    data, addr=serverUDPsock.recvfrom(2048)
    
    if data.decode('utf-8') == "Bye":
        print("All the data has been successfully received")
        break

    rcvdsqn=int(data[0:32],2)
    checksumRcvd=int(data[32:48],2)
    payload=data[64:]

    if rcvdsqn > expectedsqn or checksum(payload, len(payload))!=checksumRcvd:
        continue
    elif rcvdsqn < expectedsqn:
        sendack='{:032b}'.format(rcvdsqn)+'{:016b}'.format(zeropad)+'{:016b}'.format(ackidentifier)
        serverUDPsock.sendto(sendack.encode('utf-8'),addr)
    elif rcvdsqn == expectedsqn and ((random.randint(0,100)/100) <= LossProb ):
        print("Packet loss, sequence number = ",expectedsqn)
    elif rcvdsqn == expectedsqn:
        sendack='{:032b}'.format(expectedsqn)+'{:016b}'.format(zeropad)+'{:016b}'.format(ackidentifier)
        serverUDPsock.sendto(sendack.encode('utf-8'),addr)
        f.write(payload.decode('utf-8'))
        expectedsqn+=1

serverUDPsock.close()
f.close()