import socket, sys
import time, os
from utils import sendfolders, recvfolders, readline
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
eventset = set()

def on_created(event):
	eventset.add((event.src_path, '', 'created'))
	print(f"Someone created {event.src_path}!")
 
def on_deleted(event):
	eventset.add((event.src_path, '', 'deleted'))
	print(f"Someone deleted {event.src_path}!")
 
def on_modified(event):
    if not os.isdir(event.src_path):
        eventset.add((event.src_path, '', 'modified'))
    print(f"hey, {event.src_path} has been modified")
 
def on_moved(event):
	eventset.add((event.src_path, event.dest_path, 'moved'))
	print(f"someone moved {event.src_path} to {event.dest_path}")


if __name__ == "__main__":
	ip = sys.argv[1]
	port = sys.argv[2]
	directory = sys.argv[3]
	timesleep = sys.argv[4]
	key = ''
	if len(sys.argv) > 5 :
		key = sys.argv[5]
	my_event = PatternMatchingEventHandler(["*"], None, False, True)
	
	my_event.on_created = on_created
	my_event.on_deleted = on_deleted
	my_event.on_modified = on_modified
	my_event.on_moved = on_moved
	
	my_observer = Observer()
	my_observer.schedule(my_event, directory, recursive=True)
	my_observer.start()
	first = 1

	try:
		while True:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			#s.connect('10.0.2.7', 12345)
			s.connect((ip, int(port)))
			s.settimeout(5)
			if first == 1 :
				if len(sys.argv) > 5 :
					s.send(key.encode('utf-8'))
					recvfolders(s, directory)
				else :
					s.send('Hi'.encode('utf-8'))
					key = s.recv(128).decode('utf-8')
					os.makedirs(key, exist_ok=True)
					sendfolders(s, directory)
			
			for event in eventset :
                eventhappenend(event[2], s, directory, event[0], event[1])
                    
			eventset.clear()
			
			first = 0
			time.sleep(int(timesleep))
	except KeyboardInterrupt:
		my_observer.stop()
	my_observer.join()

def sendfile(s, keyfoldername, filename):
    s.send(filename + '\n')
    relpath = os.path.relpath(filename, keyfoldername)
    filesize = os.path.getsize(filename)
    with open(filename,'rb') as f:
        s.send(relpath.encode('utf-8') + b'\n')
        s.send(str(filesize).encode('utf-8') + b'\n')

        # Send the file in chunks so large files can be handled.
        data = f.read(chunk)
        while data:
            s.send(data)
            data = f.read(chunk)







