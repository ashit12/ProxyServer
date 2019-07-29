import socket
import sys
import threading
import signal
import time
import os
from datetime import datetime

class Server:
	def __init__(self, port):
		self.SERVER_NAME = "Nex - Simple HTTP server/v.0.3"
		self.SERVER_SHORT_NAME = "Nex/v.0.4"
		self.HOST_NAME = "0.0.0.0"
		self.BIND_PORT = port
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
		self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		# Re-use the socket
		self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		# bind the socket to a public host, and a port   
		self.serverSocket.bind((self.HOST_NAME, self.BIND_PORT))
		
		self.serverSocket.listen(10) # become a server socket
		self.__clients = {}
		self.client_no = 0

	def listenToClient(self):
		while True:

			# Establish the connection
			(clientSocket, client_address) = self.serverSocket.accept() 
			
			d = threading.Thread(name=self.getClientName(client_address), 
			target = self.ServerThread, args=(clientSocket, client_address))
			d.setDaemon(True)
			d.start()

	def getClientName(self, cli_addr):
		""" Return the clientName with appropriate number.
		If already an old client then get the no from map, else
		assign a new number.
		"""
		lock = threading.Lock()
		lock.acquire()
		ClientAddr = cli_addr[0]
		if ClientAddr in self.__clients:
			lock.release()
			return "Client-" + str(self.__clients[ClientAddr])

		self.__clients[ClientAddr] = self.client_no
		self.client_no += 1
		lock.release()
		return "Client-" + str(self.__clients[ClientAddr])

	def ServerThread(self, conn, client_addr):
		
		# get the request from browser
		request = conn.recv(self.MAX_REQUEST_LEN) 
		# print request

		# parse the first line
		first_line = request.split('\n')[0]

		# print first_line

		temp = first_line.split(' ')[1]

		filename = temp.split('/')[1]

		last_line = request.split('\n')[-1]
		cache_mod_time = int(float(last_line.split(' ')[1]))

		if cache_mod_time > 0:
			cache_mod_time = time.strftime('%H:%M:%S', time.localtime(cache_mod_time))

			file_mod_time = time.ctime(os.path.getmtime(filename))
			file_mod_time = file_mod_time.split(' ')[4]

			FMT = '%H:%M:%S'
			print cache_mod_time, type(cache_mod_time), file_mod_time, type(file_mod_time)
			tdelta = datetime.strptime(cache_mod_time, FMT) - datetime.strptime(file_mod_time, FMT)
			print tdelta.seconds

			if tdelta.seconds <= 43200:
				data = "HTTP/1.1 304 OK\nContent-Type: text/plain\nContent-Length: 12\n\n"
				conn.send(data)
				return

		header = "HTTP/1.1 200 OK\nContent-Type: text/plain\nContent-Length: 12\n\n"
		try:
			f = open(filename, "rb")
			data = ""
			while True:
				chunk = f.read()
				if not len(chunk):
					break
				data += chunk
			f.close()

		except:
			data = "File not found"
			conn.send(data)
			return

		# data = "HTTP/1.1 200 OK\nContent-Type: text/plain\nContent-Length: 12\n\nWelcome to server " + str(self.BIND_PORT)
		data = header + data
		# print data
		conn.send(data) # send to browser/client
		print "data sent"
		# 		else:
		# 			break
		# except:
		# 	pass

	def shutdown(self, signum, frame):
		""" Handle the exiting server. Clean all traces """

		self.log("WARNING", -1, 'Shutting down gracefully...')
		main_thread = threading.currentThread()        # Wait for all clients to exit
		for t in threading.enumerate():
			if t is main_thread:
				continue
			self.log("FAIL", -1, 'joining ' + t.getName())
			t.join()
		self.serverSocket.close()
		sys.exit(0)

if __name__ == '__main__':
	port = 20102
	server = Server(port)
	server.listenToClient()
