import socket
import sys
import random
import string
import os
from utils import sendfolders, recvfolders, recvchanges, eventhappenend, readline


# get new id for a new computer
def get_computer_id(map_clients):
	id = ''
	flag = True
	while flag:
		id = ''.join(random.choice(string.digits) for i in range(7))
		flag = False
		for client_changes in map_clients.values():
			if id in client_changes.keys():
				flag = True
				break
	map_key_of_map_client_and_changes[key] = {computer_id: None}
	return id


# get new id for a new client
def get_client_id():
	key = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(128))
	while os.path.isdir(key):
		key = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(128))
	return key


if __name__ == "__main__":
	name, port = sys.argv
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.bind(('', int(port)))
	server.listen(3)
	map_key_of_map_client_and_changes = {}
	computer_id = 0
	key = ''

	while True:
		client_socket, client_address = server.accept()
		print('Connection from: ', client_address)
		data = client_socket.recv(129).decode('utf-8')

		# new client
		if data == 'Hi':
			# rand a computer id and client id and send it to the client
			computer_id = get_computer_id(map_key_of_map_client_and_changes)
			key = get_client_id()
			client_socket.send(computer_id.encode('utf-8'))
			client_socket.send(key.encode('utf-8'))

			# receive from the client the back-up folder
			try:
				recvfolders(client_socket, key)
			except:
				print("receive folders failed")
		else:

			# new computer of an existing client
			if data[0] == 'n':
				# rand a computer id
				computer_id = get_computer_id(map_key_of_map_client_and_changes)

				# send the computer its new id
				try:
					client_socket.send(computer_id.encode('utf-8'))
					sendfolders(client_socket, data[1:])
				except:
					print("send folders failed")

			# existing computer
			else:
				computer_id = client_socket.recv(7).decode('utf-8')

				# send the changes in the back-up folder of the client account
				if map_key_of_map_client_and_changes[key][computer_id] is not None:
					client_socket.send('updates from another computer'.encode('utf8') + b'\n')
					for event in map_key_of_map_client_and_changes[key][computer_id]:
						eventhappenend(event[2], client_socket, data[1:], event[0], event[1])
					map_key_of_map_client_and_changes[key][computer_id] = None
				else:
					client_socket.send('receive changes from client'.encode('utf8') + b'\n')

				# receive the changes in the back-up folder of the client
				size = int(readline(client_socket))
				if size > 0:
					try:
						recvchanges(client_socket, data[1:], map_key_of_map_client_and_changes, computer_id)
					except:
						print("receive changes failed")

		print('Client disconnected')


