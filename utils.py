import os
import shutil
chunk = 1000000


def sendfolders(client, keyfoldername):
	with client:
		client.send(os.sep.encode() + b'\n')
		for path, dirs, files in os.walk(keyfoldername):
			for d in dirs:
				dirname = os.path.join(path, d)
				relpathdir = os.path.relpath(dirname, keyfoldername)
				dirsize = 0
				client.send(relpathdir.encode('utf-8') + b'\n')
				client.send(str(dirsize).encode('utf-8') + b'\n')

			for file1 in files:
				filename = os.path.join(path, file1)
				relpath = os.path.relpath(filename, keyfoldername)
				filesize = os.path.getsize(filename)

				print(f'Sending {relpath}')

				with open(filename, 'rb') as f:
					client.send(relpath.encode('utf-8') + b'\n')
					client.send(str(filesize).encode('utf-8') + b'\n')

					# Send the file in chunks so large files can be handled.
					data = f.read(chunk)
					while data:
						client.send(data)
						data = f.read(chunk)
	print('Done')


def recvchanges(sock, foldername):
	with sock:
		while True:
			rec = readline(sock)
			if not rec:
				break

			change = rec.strip()
			eventrecieved(change, sock, foldername)


def recvfolders(sock, foldername):
	count = 0
	seperator = os.sep
	with sock:
		while True:
			rec = readline(sock)
			if not rec:
				break
			if count == 0:
				seperator = rec
				rec = readline(sock)
			count = count + 1

			filename = rec.strip()
			length = int(readline(sock))
			path = foldername
			for dirname in filename.split(seperator):
				path = os.path.join(path, dirname)
			print(f'Downloading {path}...\n  Expecting {length:,} bytes...', end='', flush=True)

			if length == 0:
				os.makedirs(path, exist_ok=True)
				print('Complete')
				continue
			os.makedirs(os.path.dirname(path), exist_ok=True)

			# Read the data in chunks so it can handle large files.
			with open(path, 'wb') as f:
				while length:
					chunkdata = min(length, chunk)
					data = sock.recv(chunkdata)
					if not data:
						break
					f.write(data)
					length -= len(data)
				else:  # only runs if while doesn't break and length==0
					print('Complete')
					continue

			# socket was closed early.
			print('Incomplete')
			break 


def readline(sock):
	rec = sock.recv(1).decode('utf-8')
	while '\n' not in rec and rec:
		rec += sock.recv(1).decode('utf-8')
	if rec:
		return rec[:-1]
	return ''


def recvcreate(s, keyfoldername):
	rec = readline(s)
	if not rec:
		return
	seperator = rec
	rec = readline(s)
	filename = rec.strip()
	length = int(readline(s))
	path = keyfoldername
	for dirname in filename.split(seperator):
		path = os.path.join(path, dirname)
	print(f'Downloading {path}...\n  Expecting {length:,} bytes...', end='', flush=True)

	if length == 0:
		os.makedirs(path, exist_ok=True)
		print('Complete')
		return
	os.makedirs(os.path.dirname(path), exist_ok=True)

	# Read the data in chunks so it can handle large files.
	with open(path, 'wb') as f:
		while length:
			chunkdata = min(length, chunk)
			data = s.recv(chunkdata)
			if not data:
				return
			f.write(data)
			length -= len(data)
		else:  # only runs if while doesn't break and length==0
			print('Complete')


def recvdelete(s):
	rec = readline(s)
	os.remove(rec)


def recvmove(s):
	src = readline(s)
	dst = readline(s)
	shutil.move(src, dst)


def senddelete(s, src):
	s.send('delete'.encode('utf-8') + b'\n')
	s.send(src.encode('utf-8') + b'\n')


def sendmove(s, src, dst):
	s.send('moved'.encode('utf-8') + b'\n')
	s.send(src.encode('utf-8') + b'\n')
	s.send(dst.encode('utf-8') + b'\n')


def sendcreate(s, keyfoldername, src):
	s.send('create'.encode('utf-8') + b'\n')
	s.send(os.sep.encode() + b'\n')

	if os.path.isdir(src):
		relpathdir = os.path.relpath(src, keyfoldername)
		dirsize = 0
		s.send(relpathdir.encode('utf-8') + b'\n')
		s.send(str(dirsize).encode('utf-8') + b'\n')

	else:
		relpath = os.path.relpath(src, keyfoldername)
		filesize = os.path.getsize(src)

		print(f'Sending {relpath}')
		with open(src, 'rb') as f:
			s.send(relpath.encode('utf-8') + b'\n')
			s.send(str(filesize).encode('utf-8') + b'\n')

			# Send the file in chunks so large files can be handled.
			data = f.read(chunk)
			while data:
				s.send(data)
				data = f.read(chunk)


def sendmodify(s, keyfoldername, src):
	s.send('modify'.encode('utf-8') + b'\n')
	s.send(os.sep.encode() + b'\n')

	if os.path.isdir(src):
		relpathdir = os.path.relpath(src, keyfoldername)
		dirsize = 0
		s.send(relpathdir.encode('utf-8') + b'\n')
		s.send(str(dirsize).encode('utf-8') + b'\n')

	else:
		relpath = os.path.relpath(src, keyfoldername)
		filesize = os.path.getsize(src)

		print(f'Sending {relpath}')
		with open(src, 'rb') as f:
			s.send(relpath.encode('utf-8') + b'\n')
			s.send(str(filesize).encode('utf-8') + b'\n')

			# Send the file in chunks so large files can be handled.
			data = f.read(chunk)
			while data:
				s.send(data)
				data = f.read(chunk)


def eventhappenend(option, s, directory, src, dst):
	switch = {
		'created': sendcreate(s, directory, src),
		'deleted': senddelete(s, directory),
		'moved': sendmove(s, src, dst),
		'modified': sendmodify(s, directory, src)
		}
	return switch.get(option)


def eventrecieved(option, s, foldername):
	switch = {
		'create': recvcreate(s, foldername),
		'delete': recvdelete(s),
		'move': recvmove(s),
		'modify': recvcreate(s, foldername)  # same like the function recieve create
		}
	return switch.get(option)
