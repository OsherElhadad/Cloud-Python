import socket, sys, random, string
import time, os

def sendfolders(client, keyfoldername) :
	with client:
		for path,dirs,files in os.walk('server'):
            		for d in dirs:
            			dirname = os.path.join(path,d)
            			relpathdir = os.path.relpath(dirname,'server')
            			dirsize = 0
            			client.send(relpathdir.encode('utf-8') + b'\n')
            			client.send(str(dirsize).encode('utf-8') + b'\n')
            		for file1 in files:
                		filename = os.path.join(path,file1)
                		relpath = os.path.relpath(filename,'server')
                		filesize = os.path.getsize(filename)

                		print(f'Sending {relpath}')

                		with open(filename,'rb') as f:
                    			client.send(relpath.encode('utf-8') + b'\n')
                    			client.send(str(filesize).encode('utf-8') + b'\n')

                    			# Send the file in chunks so large files can be handled.
                    			data = f.read(100000)
                    			while data:
                        			client.send(data)
                        			data = f.read(100000)
	print('Done.')

def recvfolder(sock, foldername) :
	with sock:
		while True:
			rec = readline(sock)
			if not rec:
				break # no more files, server closed connection.

			filename = rec.strip()
			length = int(readline(sock))
			print(f'Downloading {filename}...\n  Expecting {length:,} bytes...',end='',flush=True)

			path = os.path.join(foldername,filename)
			if length == 0 :
				os.makedirs(path,exist_ok=True)
				print('Complete')
				continue
			os.makedirs(os.path.dirname(path),exist_ok=True)

        		# Read the data in chunks so it can handle large files.
			with open(path,'wb') as f:
        			while length:
        				chunk = length
        				data = sock.recv(chunk)
        				if not data: break
        				f.write(data)
        				length -= len(data)
        			else: # only runs if while doesn't break and length==0
        				print('Complete')
        				continue

        		# socket was closed early.
			print('Incomplete')
			break 

def readline(sock) :
	rec = sock.recv(1).decode('utf-8')
	while '\n' not in rec and rec :
		rec += sock.recv(1).decode('utf-8')
	if rec :
		return rec[:-1]
	return ''

if __name__ == "__main__":
	port = sys.args[1]
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.bind(('10.0.2.7', port))
	server.listen(5)
	keys = {}
	while True:
		client_socket, client_address = server.accept()
		print('Connection from: ', client_address)
		data = client_socket.recv(128)
		if data.decode('utf-8') == 'Hi' :
			key = ''.join(rendom.choice(string.ascii_letters + string.digits) for i in range(128))
			client_socket.send(key)
			recvfolder(server, key)
		else :
			pass
		print('Client disconnected')
