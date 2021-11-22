import socket
import sys
import random
import string
import os
from utils import sendfolders, recvfolders, recvchanges, eventhappenend, readline

if __name__ == "__main__":
	name, port = sys.argv
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.bind(('', int(port)))
	server.listen(5)
	mapkeyofmapclientandchanges = {}
	clientid = 0
	while True:
		client_socket, client_address = server.accept()
		print('Connection from: ', client_address)
		data = client_socket.recv(129).decode('utf-8')
		if data == 'Hi':
			flag = True
			while flag:
				clientid = ''.join(random.choice(string.digits) for i in range(7))
				flag = False
				for clientchanges in mapkeyofmapclientandchanges.values():
					for cid in clientchanges.keys():
						if cid == clientid:
							flag = True
							break
			key = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(128))
			while os.path.isdir(key):
				key = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(128))
			mapkeyofmapclientandchanges[key] = {clientid: None}
			client_socket.send(clientid.encode('utf-8'))
			client_socket.send(key.encode('utf-8'))
			try:
				recvfolders(client_socket, key)
			except:
				print("receive folders failed")
		else:
			if data[0] == 'n':
				flag = True
				while flag:
					clientid = ''.join(random.choice(string.digits) for i in range(7))
					flag = False
					for clientchanges in mapkeyofmapclientandchanges.values():
						for cid in clientchanges.keys():
							if cid == clientid:
								flag = True
								break
				mapkeyofmapclientandchanges[key] = {clientid: None}
				try:
					client_socket.send(clientid.encode('utf-8'))
					sendfolders(client_socket, data[1:])
				except:
					print("send folders failed")
			else:
				clientid = client_socket.recv(7).decode('utf-8')
				if mapkeyofmapclientandchanges[key][clientid] is not None:
					client_socket.send('updates from another computer'.encode('utf8') + b'\n')
					for event in mapkeyofmapclientandchanges[key][clientid]:
						eventhappenend(event[2], client_socket, data[1:], event[0], event[1])
					mapkeyofmapclientandchanges[key][clientid] = None
				else:
					client_socket.send('receive changes from client'.encode('utf8') + b'\n')
				size = int(readline(client_socket))
				if size > 0:
					try:
						recvchanges(client_socket, data[1:], mapkeyofmapclientandchanges, clientid)
					except:
						print("receive changes failed")

		print('Client disconnected')
