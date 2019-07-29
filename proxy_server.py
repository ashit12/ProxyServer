import socket
import signal
import threading
import sys
from time import time

class Server:
    """ A class for the proxy-server which will listen to connections from the client
    and attach sockets to them. Also supports caching of responses and blacklisted domains
    with authenticated access to them."""
    def __init__(self):

        self.HOST_NAME = "127.0.0.1"
        self.BIND_PORT = 20100
        self.MAX_REQUEST_LEN = 1024
        self.PROXY_SERVER = False
        self.CONNECTION_TIMEOUT = 5
        self.STATUS_STRING = {
            200 : "200 OK",
            206 : "206 Partial Content",
            403 : "403 Forbidden",
            404 : "404 Not Found",
            500 : "500 Server Error"
        }
        signal.signal(signal.SIGINT, self.shutdown) 

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.HOST_NAME, self.BIND_PORT))        
        self.sock.listen(10) # become a server socket
        self.client_no = 0
        self.__clients = {}

        self.request_timestamp  = {}

        self.cache = {}

        f = open("blacklist.txt", "rb")
        data = ""
        while True:
            chunk = f.read()
            if not len(chunk):
                break
            data += chunk
        f.close()
        self.BLACKLIST_DOMAINS = data.splitlines()

        f = open("auth.txt", "rb")
        data = ""
        while True:
            chunk = f.read()
            if not len(chunk):
                break
            data += chunk
        f.close()
        self.Auth = data.splitlines()

    def listenToClient(self):
        """Helper function which accepts a socket connection from a client
        and uses a thread to serve it"""
        while True:
            (clientsock, clientadd) = self.sock.accept() 
            thrd = threading.Thread(name=self.getClientName(clientadd),target=self.proxyThread,args=(clientsock,clientadd))
            thrd.setDaemon(True)
            thrd.start()

    def getClientName(self, cli_addr):
        """ Return the clientName with appropriate number.
        If already an old client then get the no from map, else
        assign a new number.
        """
        lock = threading.Lock()
        lock.acquire()
        clienttaddr = cli_addr[0]
        if clienttaddr in self.__clients:
            lock.release()
            return "Client-" + str(self.__clients[clienttaddr])

        self.__clients[clienttaddr] = self.client_no
        self.client_no += 1
        lock.release()
        return "Client-" + str(self.__clients[clienttaddr])

    def proxyThread(self, conn, client_addr):
        request = conn.recv(self.MAX_REQUEST_LEN) 
        first_line = request.split('\n')[0]
        url = first_line.split(' ')[1]

        if url in self.BLACKLIST_DOMAINS:
            fourth_line = request.split('\n')[3]
            fifth_line = request.split('\n')[4]
            Uname = fourth_line.split(' ')[1]
            Password = fifth_line.split(' ')[1]
            if Uname + ' ' + Password not in self.Auth:
                data = "This site is blocked\n"
                conn.send(data)
                return

        if url in self.cache:
            request += 'If-Modified-Since: ' + str(self.cache[url][0])
        else:
            request += 'If-Modified-Since: ' + '0'

        http_pos = url.find("://") # find pos of ://
        if (http_pos==-1):
            temp = url
        else:
            temp = url[(http_pos+3):] # get the rest of url

        port_pos = temp.find(":") # find the port pos (if any)

        webserver_pos = temp.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp)

        webserver = ""
        port = -1
        if (port_pos==-1 or webserver_pos < port_pos): 
            port = 80 
            webserver = temp[:webserver_pos] 

        else: # specific port 
            port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
            webserver = temp[:port_pos] 

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        s.settimeout(self.CONNECTION_TIMEOUT)
        # print port
        s.connect((webserver, port))
        s.sendall(request)

        try:
            while 1:
                data = s.recv(self.MAX_REQUEST_LEN)
                if data != "File not found":
                    first_line = data.split('\n')[0]
                    return_status = first_line.split(' ')[1]
                    print return_status
                    if return_status == '304':
                        conn.send(self.cache[url][1])
                        return

                    cur_time = time()
                    try:
                        if len(self.request_timestamp[url]) == 3:
                            del self.request_timestamp[url][0]
                        self.request_timestamp[url].append([cur_time, data])

                        if len(self.request_timestamp[url]) == 3:
                            time_diff = self.request_timestamp[url][2][0] - self.request_timestamp[url][0][0]
                            if time_diff < 300:
                                if len(self.cache) < 3:
                                    self.cache[url] = self.request_timestamp[url][2]
                                else:
                                    min_url = ''
                                    min_time = float('inf')
                                    for i in self.cache:
                                        if self.cache[i][0] < min_time:
                                            min_time = self.cache[i][0]
                                            min_url = i

                                    del self.cache[min_url]
                                    self.cache[url] = self.request_timestamp[url][2]
                    except:
                        self.request_timestamp[url] = []
                        self.request_timestamp[url].append([cur_time, data])
                    print self.cache
                    if (len(data) > 0):
                        conn.send(data)
                else:
                    header = "HTTP/1.1 200 OK\nContent-Type: text/plain\nContent-Length: 12\n\n"
                    if (len(data) > 0):
                        conn.send(header + data) # send to browser/client
                    else:
                        break
        except:
            pass

    def shutdown(self, signum, frame):
        """ Remove all existing sockets before shutting down the programs"""

        self.log("WARNING", -1, 'Shutting down gracefully...')
        main_thread = threading.currentThread()
        for t in threading.enumerate():
            if t is main_thread:
                continue
            self.log("FAIL", -1, 'joining ' + t.getName())
            t.join()
        self.sock.close()
        sys.exit(0)

if __name__ == "__main__":
    server = Server()
    server.listenToClient()