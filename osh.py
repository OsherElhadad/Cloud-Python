import os, socket

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
	foldername = 'client'
	# Make a directory for the received files.
	os.makedirs(foldername,exist_ok=True)

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect(('25.39.253.118',12345))
	sock.settimeout(0.1)
	recvfolder(sock, foldername)

