import os, socket, shutil
chunk = 1000000

def sendfolders(client, keyfoldername) :
	with client:
		client.send(os.sep.encode() + b'\n')
		for path,dirs,files in os.walk(keyfoldername):
            for d in dirs:
            	dirname = os.path.join(path,d)
            	relpathdir = os.path.relpath(dirname,keyfoldername)
            	dirsize = 0
            	client.send(relpathdir.encode('utf-8') + b'\n')
            	client.send(str(dirsize).encode('utf-8') + b'\n')
            for file1 in files:
               	filename = os.path.join(path,file1)
               	relpath = os.path.relpath(filename,keyfoldername)
             	filesize = os.path.getsize(filename)

                print(f'Sending {relpath}')

               	with open(filename,'rb') as f:
                  	client.send(relpath.encode('utf-8') + b'\n')
                  	client.send(str(filesize).encode('utf-8') + b'\n')

                  	# Send the file in chunks so large files can be handled.
                   	data = f.read(chunk)
                   	while data:
                    client.send(data)
                    data = f.read(chunk)
	print('Done.')

def recvchanges(sock, foldername) :
	with sock:
		count = 0
		seperator = os.sep
		while True:
			rec = readline(sock)
			if not rec:
				break # no more change, server closed connection.

			change = rec.strip()
            eventrecieved(change, sock, foldername)
	
def recvfolders(sock, foldername) :
	with sock:
		count = 0
		seperator = os.sep
		while True:
			rec = readline(sock)
			if not rec:
				break # no more files, server closed connection.
			if count == 0 :
				seperator = rec
				rec = readline(sock)
			count = count + 1

			filename = rec.strip()
			length = int(readline(sock))
			path = foldername
			for dirname in filename.split(seperator) :
				path = os.path.join(path,dirname)
			print(f'Downloading {path}...\n  Expecting {length:,} bytes...',end='',flush=True)

			if length == 0 :
				os.makedirs(path,exist_ok=True)
				print('Complete')
				continue
			os.makedirs(os.path.dirname(path),exist_ok=True)

        		# Read the data in chunks so it can handle large files.
			with open(path,'wb') as f:
        			while length:
        				chunkdata = min(length, chunk)
        				data = sock.recv(chunkdata)
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

def create(s, keyfoldername, filename):
    s.send('create\n')
	client.send(os.sep.encode() + b'\n')
    relpath = os.path.relpath(filename, keyfoldername)
    filesize = os.path.getsize(filename)
    with open(filename,'rb') as f:
        client.send(relpath.encode('utf-8') + b'\n')
        client.send(str(filesize).encode('utf-8') + b'\n')

        # Send the file in chunks so large files can be handled.
        data = f.read(chunk)
        while data:
            client.send(data)
            data = f.read(chunk)

def recvcreate(s, keyfoldername, filename):
	rec = readline(sock)
	if not rec:
		break # no more files, server closed connection.
	seperator = rec
	rec = readline(sock)
    filename = rec.strip()
	length = int(readline(sock))
	path = keyfoldername
	for dirname in filename.split(seperator) :
		path = os.path.join(path,dirname)
	print(f'Downloading {path}...\n  Expecting {length:,} bytes...',end='',flush=True)

	if length == 0 :
		os.makedirs(path,exist_ok=True)
		print('Complete')
		continue
	os.makedirs(os.path.dirname(path),exist_ok=True)

    # Read the data in chunks so it can handle large files.
	with open(path,'wb') as f:
       	while length:
        	chunkdata = min(length, chunk)
        	data = sock.recv(chunkdata)
       		if not data: break
            f.write(data)
        	length -= len(data)
       	else: # only runs if while doesn't break and length==0
        	print('Complete')

def recvdelete(s, directory):
    rec = readline(s)
    os.remove(rec)

def recvmove(s, directory):
    src = readline(s)
    dst = readline(s)
    shutil.move(src, dst)

def delete(src):
    s.send('delete\n')
    s.send(src + '\n')

def move(src, dst):
    s.send('moved\n')
    s.send(src + '\n')
    s.send(dst + '\n')

def modify(s, keyfoldername, filename):
    s.send('modify\n')
	client.send(os.sep.encode() + b'\n')
    relpath = os.path.relpath(filename, keyfoldername)
    filesize = os.path.getsize(filename)
    with open(filename,'rb') as f:
        client.send(relpath.encode('utf-8') + b'\n')
        client.send(str(filesize).encode('utf-8') + b'\n')

        # Send the file in chunks so large files can be handled.
        data = f.read(chunk)
        while data:
            client.send(data)
            data = f.read(chunk)

def eventhappenend(option, s, directory, src, dst):
    switch = {
       'created': create(s, directory, src),
       'deleted': delete(src),
       'moved': move(s, directory, src),
       'modified': modify(src, dst)
       }
    return switch.get(option)

def eventrecieved(option, s, directory):
    switch = {
       'create': recvcreate(s, directory),
       'delete': recvdelete(s, directory),
       'move': recvmove(s, directory),
       'modify': recvcreate(s, directory) # same like the function recieve create
       }
    return switch.get(option)
