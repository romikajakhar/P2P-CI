import socket
import threading
import platform
import mimetypes
import os
import sys
import time
from pathlib import Path


class P2P_Exception(Exception):
    pass


class Client(object):
    def __init__(self, ServerHost='127.0.0.1', Version='P2P-CI/1.0', dir='RFC_LIST'):  # Constructor
        self.ServerHost = ServerHost  # In this project we consider only localhost
        self.ServerPort = 7734  # Port Address of the Server
        self.Version = Version  # Current Supported Version
        self.Upload_Port = None  # Upload Port of the Client
        self.dir = 'RFC_LIST'  # file directory
        Path(self.dir).mkdir(exist_ok=True)
        self.To_be_Shared = True  # Interprocess To_be_Shareds

    def start(self):  # Start Connection to the Server
        print('Connecting to the server %s on Port : %s' % (self.ServerHost, self.ServerPort))
        self.server = socket.socket(socket.AF_INET,
                                    socket.SOCK_STREAM)  # Create an IPV4-TCP socket object to connect to the server
        try:  # Initiate Connection to the server
            self.server.connect((self.ServerHost, self.ServerPort))
        except Exception:  # On Unsuccessful connection throw an error
            print('Server Unavailable')
            return
        upload_process = threading.Thread(target=self.Pre_upload)  # Create a new process
        upload_process.start()
        while self.Upload_Port is None:  # Wait until the upload port is initialized
            pass
        print('Connected via Port: %s' % self.Upload_Port)  # Connection to Server is Successfullvia upload port
        self.Client_Requests()  # Initiate Requests

    def Client_Requests(self):  # Request a Service
        Request_Methods = {'1': self.ADD, '2': self.LOOKUP, '3': self.LIST_ALL, '4': self.DOWNLOAD, '5': self.TERMINATE}
        while True:
            try:
                print('Choose A Request Type ')
                req = input('\n 1: Add\n 2: Look Up\n 3: List All\n 4: GetRFC\n 5: Terminate\n')
                Request_Methods.setdefault(req,
                                           self.Invalid_Command)()  # Service the Request and If requested for Unavailable service throw an error
            except P2P_Exception as e:  # Handle the Exceptions
                print(e)
            except Exception:  # Handle System-Exiting Exceptions
                print('System Error.')
            except BaseException:  # Handle System-Exiting Exceptions
                print('Unexpected Error!\n Terminating')
                self.TERMINATE()

    def ADD(self, rfc=None, title=None):  # Subroutine to ADD RFC to the server database
        if not rfc:
            rfc = input('Enter the RFC number to be added:')  # Get the RFC rfcmber to be added
            if not rfc.isdigit():  # If Valid number is not entered throw an error
                raise P2P_Exception('Invalid Input.')
            title = input('Enter the RFC title: ')
        file = Path('%s/rfc%s.txt' % (self.dir, rfc))
        print(file)
        if not file.is_file():
            raise P2P_Exception('File doesn\'t Not Exist')
        msg = 'ADD RFC %s %s\n' % (rfc, self.Version)
        msg += 'Host: %s\n' % socket.gethostname()
        msg += 'Port: %s\n' % self.Upload_Port
        msg += 'Title: %s\n' % title
        self.server.sendall(msg.encode())
        res = self.server.recv(1024).decode()
        print('Recieve response: \n%s' % res)

    def LOOKUP(self):  # Subroutine to Look Up an RFC from the server database
        rfc = input('Enter the RFC number: ')
        title = input('Enter the RFC title(optional): ')
        msg = 'LOOKUP RFC %s %s\n' % (rfc, self.Version)
        msg += 'Host: %s\n' % socket.gethostname()
        msg += 'Port: %s\n' % self.Upload_Port
        msg += 'Title: %s\n' % title
        self.server.sendall(msg.encode())
        res = self.server.recv(1024).decode()
        print('Recieve response: \n%s' % res)

    def LIST_ALL(self):  # Subroutine to List all the RFCs present in the server database
        l1 = 'LIST ALL %s\n' % self.Version
        l2 = 'Host: %s\n' % socket.gethostname()
        l3 = 'Port: %s\n' % self.Upload_Port
        msg = l1 + l2 + l3
        self.server.sendall(msg.encode())
        res = self.server.recv(1024).decode()
        print('Recieve response: \n%s' % res)

    def DOWNLOAD(self):  # Subroutine to initiate download of an RFC from a peer
        rfc = input('Enter the RFC number: ')
        msg = 'LOOKUP RFC %s %s\n' % (rfc, self.Version)
        msg += 'Host: %s\n' % socket.gethostname()
        msg += 'Port: %s\n' % self.Upload_Port
        msg += 'Title: Unknown\n'
        self.server.sendall(msg.encode())
        lines = self.server.recv(1024).decode().splitlines()
        if lines[0].split()[1] == '200':
            print('Requested RFC is Available in Peers: ')  # Select a peer to download from
            for i, line in enumerate(lines[1:]):
                line = line.split()
                print('%s: %s:%s' % (i + 1, line[-2], line[-1]))

            try:
                idx = int(input('Choose a peer to download RFC from: '))
                title = lines[idx].rsplit(None, 2)[0].split(None, 2)[-1]
                peer_host = lines[idx].split()[-2]
                peer_port = int(lines[idx].split()[-1])
            except Exception:
                raise P2P_Exception('Invalid Input.')
            # exclude self
            if ((peer_host, peer_port) == (socket.gethostname(), self.Upload_Port)):
                raise P2P_Exception('Do not choose yourself.')
            # send get request
            self.GetRFC(rfc, title, peer_host, peer_port)
        elif lines[0].split()[1] == '400':
            raise P2P_Exception('Invalid Input.')
        elif lines[0].split()[1] == '404':
            raise P2P_Exception('File Not Available.')
        elif lines[0].split()[1] == '500':
            raise P2P_Exception('Version Not Supported.')

    def GetRFC(self, rfc, title, peer_host, peer_port):  # Subroutine to Download RFC from a Peer
        try:
            soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create socket object to start downloading
            if soc.connect_ex((peer_host, peer_port)):
                raise P2P_Exception('Peer Not Available')
            msg = 'GET RFC %s %s\n' % (rfc, self.Version)  # Initiate the Request
            msg += 'Host: %s\n' % socket.gethostname()
            msg += 'OS: %s\n' % platform.platform()
            soc.sendall(msg.encode())
            rcvd_msg = soc.recv(1024).decode()
            print('Recieve response rcvd_msg: \n%s' % rcvd_msg)
            rcvd_msg = rcvd_msg.splitlines()
            if rcvd_msg[0].split()[-2] == '200':
                path = '%s/rfc%s.txt' % (self.dir, rfc)
                print('Downloading')
                try:
                    with open(path, 'w') as file:
                        content = soc.recv(1024)
                        while content:
                            file.write(content.decode())
                            content = soc.recv(1024)
                except Exception:
                    raise P2P_Exception('Downloading Failed')
                total_length = int(rcvd_msg[4].split()[1])
                if os.path.getsize(path) < total_length:
                    raise P2P_Exception('Downloading Failed')
                print('Downloading Completed')
                print('Sending ADD request to share')  # Share file, send ADD request
                if self.To_be_Shared:
                    self.ADD(rfc, title)
            elif rcvd_msg[0].split()[1] == '400':
                raise P2P_Exception('Invalid Input!')
            elif rcvd_msg[0].split()[1] == '404':
                raise P2P_Exception('File Not Available!')
            elif rcvd_msg[0].split()[1] == '500':
                raise P2P_Exception('Version Not Supported!')
        finally:
            soc.close()

    def Pre_upload(self):  # Subroutine to initiate Peer to Peer Communication
        self.upload = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.upload.bind(('', 0))  # Allocation of an avaialble free port or Bind to a free TCP port
        self.Upload_Port = self.upload.getsockname()[1]  # Get the Port number
        self.upload.listen(5)  # Start Listening on Upload Port
        while self.To_be_Shared:
            requester, address = self.upload.accept()
            handler = threading.Thread(target=self.Upload_Process,
                                       args=(requester, address))  # Creating a Thread to Open New Connection
            handler.start()  # Starting a thread
        self.upload.close()  # Once the function is completed close the thread

    def Upload_Process(self, soc, address):  # Peer to Peer Data transfer
        rcvd_msg = soc.recv(1024).decode().splitlines()
        try:
            version = rcvd_msg[0].split()[-1]  # Store the version
            rfc = rcvd_msg[0].split()[-2]  # Store the Port Number
            method = rcvd_msg[0].split()[0]
            path = '%s/rfc%s.txt' % (self.dir, rfc)
            if version != self.Version:
                soc.sendall(str.encode(
                    self.Version + ' 505 P2P-CI Version Not Supported!\n'))  # If the version is not supported,throw an error
            elif not Path(path).is_file():
                soc.sendall(str.encode(
                    self.Version + ' 404 Not Found!\n'))  # if the file is not found in the directory,throw an error
            elif method == 'GET':
                rcvd_msg = self.Version + ' 200 OK\n'
                rcvd_msg += 'Date: %s\n' % (time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime()))
                rcvd_msg += 'OS: %s\n' % (platform.platform())
                rcvd_msg += 'Last-Modified: %s\n' % (
                    time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(os.path.getmtime(path))))
                rcvd_msg += 'Content-Length: %s\n' % (os.path.getsize(path))
                rcvd_msg += 'Content-Type: %s\n' % (mimetypes.MimeTypes().guess_type(path)[0])
                soc.sendall(rcvd_msg.encode())
                # Uploading
                try:
                    print('\nUploading...')

                    send_length = 0
                    with open(path, 'r') as file:
                        to_send = file.read(1024)
                        while to_send:
                            send_length += len(to_send.encode())  # total_length = int(os.path.getsize(path))
                            soc.sendall(to_send.encode())
                            to_send = file.read(1024)
                except Exception:
                    raise P2P_Exception('Uploading Failed')  # if send_length < total_length: raise P2P_Exception
                print('Uploading Completed.')
                # Restore Client_Requests
                print('Choose A Request Type ')
                print('\n 1: Add\n 2: Look Up\n 3: List All\n 4: GetRFC\n 5: Terminate\n')
            else:
                raise P2P_Exception('Bad Request.')
        except Exception:
            soc.sendall(str.encode(self.Version + '  400 Bad Request\n'))
        finally:
            soc.close()

    def Invalid_Command(self):  # Throw an error when entered input value is incorrect
        raise P2P_Exception('\nInvalid Input.')

    def TERMINATE(self):  # Kill the system on exception
        print('\nTerminated')
        self.server.close()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        c = Client(sys.argv[1])  # To Connect to Host on other device
    else:
        c = Client()  # To Connect to a local host
    c.start()