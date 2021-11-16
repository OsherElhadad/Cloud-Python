from socket import *
import os

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

if __name__ == "__main__":
	sock = socket()
	sock.bind(('',12345))
	sock.listen(5)

	while True:
    		print('Waiting for a client...')
    		client,address = sock.accept()
    		print(f'Client joined from {address}')
    		sendfolders(client, 'server')

