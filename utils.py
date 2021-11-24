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
def recvchanges(sock, folder_name, size, map_key_of_map_client_and_changes=None, computer_id=0):
    while size > 0:
        try:
            rec = readline(sock)
            if not rec:
                break
            change = rec.strip()
            eventrecieved(change, sock, folder_name, map_key_of_map_client_and_changes, computer_id)
            size = size - 1
        except:
            break


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
                if map_key_of_map_client_and_changes[key_folder_name][cid] is not None:
                    map_key_of_map_client_and_changes[key_folder_name][cid].append((path, '', 'created'))
                else:
                    map_key_of_map_client_and_changes[key_folder_name][cid] = [(path, '', 'created')]
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


# receive a file modified
def receivefile(s, key_folder_name, map_key_of_map_client_and_changes=None, computer_id=0):
    separator = readline(s)
    filename = readline(s)[1:]
    length = int(readline(s))
    path = key_folder_name
    for dirname in filename.split(separator):
        path = os.path.join(path, dirname)
    if map_key_of_map_client_and_changes is not None:
        for cid in map_key_of_map_client_and_changes[key_folder_name].keys():
            if cid != computer_id:
                if map_key_of_map_client_and_changes[key_folder_name][cid] is not None:
                    map_key_of_map_client_and_changes[key_folder_name][cid].append((path, '', 'modified'))
                else:
                    map_key_of_map_client_and_changes[key_folder_name][cid] = [(path, '', 'modified')]
    print(f'Downloading {path}...\n  Expecting {length:,} bytes...', end='', flush=True)

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

# receive a report about a delete in the client's folder
def recvdelete(s, key_folder_name, map_key_of_map_client_and_changes=None, computer_id=0):
    seperator = readline(s)
    path = readline(s)
    all_path = key_folder_name
    for name in path.split(seperator):
        if name != '..' and name != '.':
            all_path = os.path.join(all_path, name)
    if map_key_of_map_client_and_changes is not None:
        for cid in map_key_of_map_client_and_changes[key_folder_name].keys():
            if cid != computer_id:
                if map_key_of_map_client_and_changes[key_folder_name][cid] is not None:
                    map_key_of_map_client_and_changes[key_folder_name][cid].append((path, '', 'deleted'))
                else:
                    map_key_of_map_client_and_changes[key_folder_name][cid] = [(path, '', 'deleted')]
    print(f'Deleting')
    if os.path.isdir(all_path):
        os.rmdir(all_path)
    else:
        os.remove(all_path)


# receive a report about a move in the client's folder
def recvmove(s, keyfoldername, map_key_of_map_client_and_changes=None, computer_id=0):
    recvcreate(s, keyfoldername, True, os.sep, map_key_of_map_client_and_changes, computer_id)
    recvdelete(s, keyfoldername, map_key_of_map_client_and_changes, computer_id)


# send about a file deleted
def senddelete(s, src):
    s.send(os.sep.encode() + b'\n')
    s.send(src.encode('utf-8') + b'\n')


# send about a new file created
def sendcreate(s, key_folder_name, src):

    if os.path.isdir(src):
        s.send(os.sep.encode() + b'\n')
        relpathdir = os.path.relpath(src, key_folder_name)
        print(f'Sending {relpathdir}')
        dirsize = 0
        s.send(b'd' + relpathdir.encode('utf-8') + b'\n')
        s.send(str(dirsize).encode('utf-8') + b'\n')

    else:
        s.send(os.sep.encode() + b'\n')
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
        s.send('modify'.encode('utf-8') + b'\n')
        s.send(os.sep.encode() + b'\n')
        return sendfile(s, directory, src)


# call the function according to the report we got
def eventrecieved(option, s, foldername, map_key_of_map_client_and_changes=None, computer_id=0):
    if option == 'create':
        return recvcreate(s, foldername, True, os.sep, map_key_of_map_client_and_changes, computer_id)
    if option == 'delete':
        return recvdelete(s, foldername, map_key_of_map_client_and_changes, computer_id)
    if option == 'move':
        return recvmove(s, foldername, map_key_of_map_client_and_changes, computer_id)
    if option == 'modify':
        return receivefile(s, foldername, map_key_of_map_client_and_changes, computer_id)
