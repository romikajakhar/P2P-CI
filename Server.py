import socket
import threading
import os
import sys
from collections import defaultdict


class Server(object):
    def __init__(self, Server_Host='127.0.0.1', Server_Port=7734, Version='P2P-CI/1.0'):  # Constructor
        self.Server_Host = Server_Host
        self.Server_Port = Server_Port
        self.Version = Version
        self.List_RFC = {}  # Create a List to maintain the RFCs present
        self.Dict_Peers = defaultdict(set)
        self.lock = threading.Lock()

    def start(self):  # Start Listening on the Port
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.bind((self.Server_Host, self.Server_Port))
            self.s.listen(5)
            print('%s Server is Up and is Listening on Port %s' % (self.Version, self.Server_Port))
            while True:
                con, address = self.s.accept()
                print('Connection Established between IP: %s via Port: %s' % (address[0], address[1]))
                thread = threading.Thread(target=self.Connect, args=(con, address))
                thread.start()
        except KeyboardInterrupt:
            print('\n Server ShutDown')
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)

    def Connect(self, con, address):  # Connect to a Client
        # keep recieve request from client
        host = None
        port = None
        while True:
            try:
                Request = con.recv(1024).decode()
                print('Received Request :\n%s' % Request)
                lines = Request.splitlines()
                version = lines[0].split()[-1]
                if version != self.Version:
                    con.sendall(str.encode(self.Version + ' 505 P2P-CI Version Not Supported\n'))
                else:
                    function = lines[0].split()[0]
                    if function == 'ADD':
                        host = lines[1].split(None, 1)[1]
                        port = int(lines[2].split(None, 1)[1])
                        num = int(lines[0].split()[-2])
                        title = lines[3].split(None, 1)[1]
                        self.ADD_TO_DICT(con, (host, port), num, title)
                    elif function == 'LOOKUP':
                        num = int(lines[0].split()[-2])
                        self.GET_PEERS(con, num)
                    elif function == 'LIST':
                        self.LIST_ALL(con)
                    else:
                        raise AttributeError('Enter Correct Request')
            except ConnectionError:
                print('IP:%s via Port: %s Disconnected' % (address[0], address[1]))
                # Clean data if necessary
                if host and port:
                    self.Remove_Peer(host, port)
                con.close()
                break
            except BaseException:
                try:
                    con.sendall(str.encode(self.Version + '  400 Bad Request\n'))
                except ConnectionError:
                    print('IP:%s via Port: %s Disconnected' % (address[0], address[1]))
                    # Clean data if necessary
                    if host and port:
                        self.Remove_Peer(host, port)
                    con.close()
                    break

    def ADD_TO_DICT(self, con, peer, num, title):  # Update the Server Database about the List of RFCs available
        self.lock.acquire()
        try:
            self.Dict_Peers[peer].add(num)
            self.List_RFC.setdefault(num, (title, set()))[1].add(peer)
        finally:
            self.lock.release()
        header = self.Version + ' 200 OK\n'
        header += 'RFC %s %s %s %s\n' % (num, self.List_RFC[num][0], peer[0], peer[1])
        con.sendall(str.encode(header))

    def Remove_Peer(self, host,
                    port):  # Upon termiantion of a Client process, Remove the peer from the Active User list and its corresponding RFC entries
        self.lock.acquire()
        nums = self.Dict_Peers[(host, port)]
        for x in nums:
            self.List_RFC[x][1].discard((host, port))
        if not self.List_RFC[x][1]:
            self.List_RFC.pop(x, None)
        self.Dict_Peers.pop((host, port), None)
        self.lock.release()

    def GET_PEERS(self, con, num):  # List of Active Peers
        self.lock.acquire()
        try:
            if num in self.List_RFC:
                header = self.Version + ' 200 OK\n'
                title = self.List_RFC[num][0]
                for peer in self.List_RFC[num][1]:
                    header += 'RFC %s %s %s %s\n' % (num, title, peer[0], peer[1])

            else:
                header = self.Version + ' 404 Not Found\n'
        finally:
            self.lock.release()
        con.sendall(str.encode(header))

    def LIST_ALL(self, con):  # Database of RFCs available and the Peers
        self.lock.acquire()
        try:
            if not self.List_RFC:
                header = self.Version + ' 404 Not Found\n'
            else:
                header = self.Version + ' 200 OK\n'
                for num in self.List_RFC:
                    title = self.List_RFC[num][0]
                    for peer in self.List_RFC[num][1]:
                        header += 'RFC %s %s %s %s\n' % (num,
                                                         title, peer[0], peer[1])
        finally:
            self.lock.release()
        con.sendall(str.encode(header))


if __name__ == '__main__':
    s = Server()  # Create a Server Socket
    s.start()  # Start the Server process