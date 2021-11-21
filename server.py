import socket
import sys
import random
import string
import os
import time
from utils import sendfolders, recvfolders, recvchanges

if __name__ == "__main__":
	name, port = sys.argv
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.bind(('', int(port)))
	server.listen(5)
	clients = {}
	while True:
		client_socket, client_address = server.accept()
		print('Connection from: ', client_address)
		data = client_socket.recv(128).decode('utf-8')
		if data == 'Hi':
			key = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(128))
			while os.path.isdir(key):
				key = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(128))
			client_socket.send(key.encode('utf-8'))
			try:
				recvfolders(client_socket, key)
			except:
				print("send failed")
		else:
			try:
				#sendfolders(client_socket, data)
				recvchanges(client_socket, data)
			except:
				print("send failed")
		""""
		data = ''
		changeset = set()
		try :
			data = readline(client_socket)
			while data:
				changeset.add(data)
				data = readline(client_socket)
		"""

		print('Client disconnected')
