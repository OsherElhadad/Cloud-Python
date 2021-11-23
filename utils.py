import os

chunk = 1000000


# send all the back-up folder to the socket
def sendfolders(s, key_folder_name):
    with s:
        s.send(os.sep.encode() + b'\n')
        for path, dirs, files in os.walk(key_folder_name):
            for d in dirs:
                sendfolder(s, path, d, key_folder_name)
            for file1 in files:
                sendfile(s, key_folder_name, os.path.join(path, file1))
    print('Done')


# receive all the changes in the back-up folder from the socket
def recvchanges(sock, folder_name, map_key_of_map_client_and_changes=None, computer_id=0):
    with sock:
        while True:
            rec = readline(sock)
            if not rec:
                break
            change = rec.strip()
            eventrecieved(change, sock, folder_name, map_key_of_map_client_and_changes, computer_id)


# receive all the back-up folder from the socket
def recvfolders(sock, folder_name):
    count = 0
    with sock:
        while True:
            if count == 0:
                flag = recvcreate(sock, folder_name, True)
                count = 1
            else:
                flag = recvcreate(sock, folder_name, False)
            if flag == 1:
                continue

            # socket was closed early.
            print('Incomplete')
            break


# read a line from the socket
def readline(s):
    rec = s.recv(1).decode('utf-8')
    while '\n' not in rec and rec:
        rec += s.recv(1).decode('utf-8')
    if rec:
        return rec[:-1]
    return ''


# receive a report about a new file in the client's folder
def recvcreate(s, key_folder_name, flag=True, separator=os.sep, map_key_of_map_client_and_changes=None, computer_id=0):
    rec = readline(s)
    if not rec:
        return -1
    if flag is True:
        separator = rec
        rec = readline(s)
    filename = rec[1:].strip()
    length = int(readline(s))
    path = key_folder_name
    for dirname in filename.split(separator):
        path = os.path.join(path, dirname)
    if map_key_of_map_client_and_changes is not None:
        for cid in map_key_of_map_client_and_changes[key_folder_name].keys():
            if cid != computer_id:
                map_key_of_map_client_and_changes[key_folder_name][cid].add((path, '', 'created'))
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


# send a folder
def sendfolder(s, path, d, key_folder_name):
    dirname = os.path.join(path, d)
    relpathdir = os.path.relpath(dirname, key_folder_name)
    dirsize = 0
    s.send(b'd' + relpathdir.encode('utf-8') + b'\n')
    s.send(str(dirsize).encode('utf-8') + b'\n')


# send a file
def sendfile(s, key_folder_name, filename):
    relpath = os.path.relpath(filename, key_folder_name)
    filesize = os.path.getsize(filename)
    print(f'Sending {relpath}')

    with open(filename, 'rb') as f:
        s.send(b'f' + relpath.encode('utf-8') + b'\n')
        s.send(str(filesize).encode('utf-8') + b'\n')

        # Send the file in chunks so large files can be handled.
        data = f.read(chunk)
        while data:
            s.send(data)
            data = f.read(chunk)


# receive a report about a delete in the client's folder
def recvdelete(s, key_folder_name):
    seperator = readline(s)
    path = readline(s)
    for name in path.split(seperator):
        key_folder_name = os.path.join(key_folder_name, name)
    print(f'Deleting')
    if os.path.isdir(key_folder_name):
        os.rmdir(key_folder_name)
    else:
        os.remove(key_folder_name)


# receive a report about a move in the client's folder
def recvmove(s, keyfoldername):
    recvcreate(s, keyfoldername)
    recvdelete(s, keyfoldername)


# send about a file deleted
def senddelete(s, src):
    s.send(os.sep.encode() + b'\n')
    s.send(src.encode('utf-8') + b'\n')


# send about a new file created
def sendcreate(s, key_folder_name, src):
    s.send(os.sep.encode() + b'\n')

    if os.path.isdir(src):
        relpathdir = os.path.relpath(src, key_folder_name)
        dirsize = 0
        s.send(b'd' + relpathdir.encode('utf-8') + b'\n')
        s.send(str(dirsize).encode('utf-8') + b'\n')

    else:
        sendfile(s, key_folder_name, src)


# call the function according to the report we want to send
def eventhappenend(option, s, directory, src, dst):
    if option == 'created':
        s.send('create'.encode('utf-8') + b'\n')
        return sendcreate(s, directory, src)
    if option == 'deleted':
        s.send('delete'.encode('utf-8') + b'\n')
        return senddelete(s, os.path.relpath(src, directory))
    if option == 'moved':
        s.send('move'.encode('utf-8') + b'\n')
        sendcreate(s, directory, dst)
        return senddelete(s, os.path.relpath(src, directory))
    if option == 'modified':
        return


# call the function according to the report we got
def eventrecieved(option, s, foldername, mapkeyofmapclientandchanges=None, computer_id=0):
    if option == 'create':
        return recvcreate(s, foldername, True, os.sep, mapkeyofmapclientandchanges, computer_id)
    if option == 'delete':
        return recvdelete(s, mapkeyofmapclientandchanges)
    if option == 'move':
        return recvmove(s.mapkeyofmapclientandchanges)
    if option == 'modify':
        return recvcreate(s, foldername, mapkeyofmapclientandchanges)