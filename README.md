## Go-back-N-Automatic-Repeat-Request-ARQ

Implement Go-back-N automatic repeat request (ARQ) scheme and carry out a number
of experiments to evaluate its performance.

Task 1: Effect of Window Size N

Task 2: Effect of MSS

Task 3: Effect of Loss Probability p

## The Simple-FTP Server (Receiver)

On the server we need to run the receiver.py file with the following argument 

$python3 receiver.py file-name p   (server will start listening on port 7735)

where "file-name" is the name of the file where the data will be written (it will create file if its not already there), 
and p is the packet loss probability needed for above given Task.


## The Simple-FTP Client (Sender)

The Sender will need to be invoked by below command 

$python3 client.py <server-IP> server-port# file-name N MSS

where server-IP is the FTP server IP where the server runs, server-port# is the port number of the server (i.e., 7735),
file-name is the name of the file to be transferred, N is the window size, and MSS is the maximum segment size.


