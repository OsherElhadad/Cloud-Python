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
				client.send(b'd' + relpathdir.encode('utf-8') + b'\n')
				client.send(str(dirsize).encode('utf-8') + b'\n')

			for file1 in files:
				filename = os.path.join(path, file1)
				relpath = os.path.relpath(filename, keyfoldername)
				filesize = os.path.getsize(filename)

				print(f'Sending {relpath}')

				with open(filename, 'rb') as f:
					client.send(b'f' + relpath.encode('utf-8') + b'\n')
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
	with sock:
		while True:
			if count == 0:
				flag = recvcreate(sock, foldername, True)
				count = 1
			else:
				flag = recvcreate(sock, foldername, False)
			if flag == 1:
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


def recvcreate(s, keyfoldername, flag=True, seperator=os.sep):
	rec = readline(s)
	if not rec:
		return -1
	if flag is True:
		seperator = rec
		rec = readline(s)
	filename = rec[1:].strip()
	length = int(readline(s))
	path = keyfoldername
	for dirname in filename.split(seperator):
		path = os.path.join(path, dirname)
	print(f'Downloading {path}...\n  Expecting {length:,} bytes...', end='', flush=True)

	if rec[0] == 'd':
		os.makedirs(path, exist_ok=True)
		print('Complete')
		return 1
	os.makedirs(os.path.dirname(path), exist_ok=True)

	# Read the data in chunks so it can handle large files.
	with open(path, 'wb') as f:
		while length:
			chunkdata = min(length, chunk)
			data = s.recv(chunkdata)
			if not data:
				break
			f.write(data)
			length -= len(data)
		else:  # only runs if while doesn't break and length==0
			print('Complete')
			return 1
	return -1


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
		s.send(b'd' + relpathdir.encode('utf-8') + b'\n')
		s.send(str(dirsize).encode('utf-8') + b'\n')

	else:
		relpath = os.path.relpath(src, keyfoldername)
		filesize = os.path.getsize(src)

		print(f'Sending {relpath}')
		with open(src, 'rb') as f:
			s.send(b'f' + relpath.encode('utf-8') + b'\n')
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
		s.send(b'd' + relpathdir.encode('utf-8') + b'\n')
		s.send(str(dirsize).encode('utf-8') + b'\n')

	else:
		relpath = os.path.relpath(src, keyfoldername)
		filesize = os.path.getsize(src)

		print(f'Sending {relpath}')
		with open(src, 'rb') as f:
			s.send(b'f' + relpath.encode('utf-8') + b'\n')
			s.send(str(filesize).encode('utf-8') + b'\n')

			# Send the file in chunks so large files can be handled.
			data = f.read(chunk)
			while data:
				s.send(data)
				data = f.read(chunk)


def eventhappenend(option, s, directory, src, dst):
	if option == 'created':
		return sendcreate(s, directory, src)
	if option == 'deleted':
		return senddelete(s, directory)
	if option == 'moved':
		return sendmove(s, src, dst)
	if option == 'modified':
		return sendmodify(s, directory, src)


def eventrecieved(option, s, foldername):
	if option == 'create':
		return recvcreate(s, foldername)
	if option == 'delete':
		return recvdelete(s)
	if option == 'move':
		return recvmove(s)
	if option == 'modify':
		return recvcreate(s, foldername)
