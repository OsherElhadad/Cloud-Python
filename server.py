import socket
import sys
import random
import string
import os
from utils import send_all, receive_folders, receive_changes, send_event, readline


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
		data = client_socket.recv(129).decode()

		# new client
		if data == 'Hi':
			# rand a computer id and client id and send it to the client
			computer_id = get_computer_id(map_key_of_map_client_and_changes)
			key = get_client_id()
			map_key_of_map_client_and_changes[key] = {computer_id: None}
			print(key)
			client_socket.send(computer_id.encode())
			client_socket.send(key.encode())

			# receive from the client the back-up folder
			try:
				receive_folders(client_socket, key)
			except:
				pass
		else:

			# new computer of an existing client
			if data[0] == 'n':
				if data[1:] not in map_key_of_map_client_and_changes.keys():
					server.close()
					break
				# rand a computer id
				computer_id = get_computer_id(map_key_of_map_client_and_changes)
				map_key_of_map_client_and_changes[data[1:]][computer_id] = None
				# send the computer its new id
				try:
					client_socket.send(computer_id.encode())
					send_all(client_socket, data[1:])
				except:
					pass

			# existing computer
			else:
				computer_id = client_socket.recv(7).decode()
				# send the changes in the back-up folder of the client account
				if map_key_of_map_client_and_changes[data[1:]][computer_id] is not None:
					client_socket.send('updates from another computer'.encode() + b'\n')
					client_socket.send(str(len(map_key_of_map_client_and_changes[data[1:]][computer_id])).encode() + b'\n')
					for event in map_key_of_map_client_and_changes[data[1:]][computer_id]:
						send_event(event[2], client_socket, data[1:], event[0], event[1])
					map_key_of_map_client_and_changes[data[1:]][computer_id] = None
				else:
					client_socket.send('receive changes from client'.encode() + b'\n')

				# receive the changes in the back-up folder of the client
				size = int(readline(client_socket))
				try:
					receive_changes(client_socket, data[1:], size, map_key_of_map_client_and_changes, computer_id)
				except:
					pass
