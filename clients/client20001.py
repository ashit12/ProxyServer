#!/usr/bin/env python  

import socket
import signal
import sys    
import getpass

class Client:

    def __init__(self):

        self.SERVER_NAME = "Nex - Simple HTTP server/v.0.3"
        self.SERVER_SHORT_NAME = "Nex/v.0.4"
        self.HOST_NAME = "127.0.0.1"
        self.BIND_PORT = 20001
        self.PROXY_SERVER = False
        self.COLORED_LOGGING = True
        self.MAX_CLIENT_BACKLOG = 50
        self.CONNECTION_TIMEOUT = 5
        self.MAX_REQUEST_LEN = 1024
        self.HOST_ALLOWED = [ "*" ]
        self.BLACKLIST_DOMAINS = [ "blocked.com" ]
        self.PUBLIC_HTML = "./public_html"
        self.ERROR_DIR = "./error_pages"
        self.OTHER_TEMPLATES = "./other_templates"
        self.STATUS_STRING = {
            200 : "200 OK",
            206 : "206 Partial Content",
            403 : "403 Forbidden",
            404 : "404 Not Found",
            500 : "500 Server Error"
        }
        # Shutdown on Ctrl+C
        signal.signal(signal.SIGINT, self.shutdown) 

        # Create a TCP socket
        self.Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Re-use the socket
        self.Socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # bind the socket to a public host, and a port  
        # print self.BIND_PORT 
        self.Socket.bind((self.HOST_NAME, self.BIND_PORT))

    def takeInput(self):
        while True:
            self.Uname = ''
            self.Password = ''
            cmd = raw_input()  
            cmd = cmd.split() 

            if len(cmd) < 2:
                print 'Enter file to be requested\n'
                continue
            
            if cmd[0] == 'exit':  
              break  

            check = raw_input('Do you want to enter Authentication Details ? (Y/N)\n')

            if check == 'Y':
                self.Uname = raw_input('Enter Username: ')
                self.Password = getpass.getpass()

            self.SendRequest(cmd)

    def SendRequest(self, cmd):

        request = 'GET localhost:' + cmd[0] + '/' + cmd[1] + ' HTTP/1.1\n'
        request += 'Host: localhost:' + cmd[0]
        request += '\nAccept-Encoding: gzip, deflate\n'
        request += 'Username: ' + self.Uname
        request += '\nPassword: ' + self.Password
        request += '\nConnection: keep-alive\n\n'

        # print request
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        s.settimeout(self.CONNECTION_TIMEOUT)
        s.connect(('127.0.0.1', 20100))
        s.sendall(request)

        try:
            while 1:
                # receive data from web server
                data = s.recv(self.MAX_REQUEST_LEN)
                temp = data.split('\n')
                temp = temp[4:len(temp)]
                for i in temp:
                    print i

                # if (len(data) > 0):
                #     conn.send(data) # send to browser/client
                # else:
                #     break
        except:
            pass

    def shutdown(self, signum, frame):
        """ Handle the exiting server. Clean all traces """

        self.log("WARNING", -1, 'Shutting down gracefully...')
        self.server.close()
        sys.exit(0)

if __name__ == "__main__":
    client = Client()
    client.takeInput()