import socket, sys
import time, os
from watchdog.observers import Observer
from watch.events import PatternMatchingEventHandler
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def on_created(event):
	s.send(event
 
def on_deleted(event):
     	print(f"what the f**k! Someone deleted {event.src_path}!")
 
def on_modified(event):
     	print(f"hey buddy, {event.src_path} has been modified")
 
def on_moved(event):
    	print(f"ok ok ok, someone moved {event.src_path} to {event.dest_path}")
    	
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
	name, ip, port, directory, time, key = sys.args
	s.connect('10.0.2.7', 12345)
	my_event = PatternMatchingEventHandler(["*"], None, False, True)
	my_event.on_created = on_created
    	my_event.on_deleted = on_deleted
    	my_event.on_modified = on_modified
    	my_event.on_moved = on_moved
    	my_observer = Observer()
    	my_observer.schedule(my_event, directory, recursive=True)
    	my_observer.start()
    	try:
        	while True:
            		time.sleep(1)
    	except KeyboardInterrupt:
        	my_observer.stop()
        	my_observer.join()



	
	s.close()
