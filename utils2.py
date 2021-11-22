import os

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


def recvchanges(sock, foldername, mapkeyofmapclientandchanges=None, clientid=0):
    with sock:
        while True:
            rec = readline(sock)
            if not rec:
                break
            change = rec.strip()
            eventrecieved(change, sock, foldername, mapkeyofmapclientandchanges, clientid)


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


def recvcreate(s, keyfoldername, flag=True, seperator=os.sep, mapkeyofmapclientandchanges=None, clientid=0):
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
    if mapkeyofmapclientandchanges is not None:
        for cid in mapkeyofmapclientandchanges[keyfoldername].keys():
            if cid != clientid:
                mapkeyofmapclientandchanges[keyfoldername][cid].add((path, '', 'created'))
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


def recvdelete(s, keyfoldername):
    seperator = readline(s)
    path = readline(s)
    for name in path.split(seperator):
        keyfoldername = os.path.join(keyfoldername, name)
    print(f'Deleting')
    if os.path.isdir(keyfoldername):
        os.rmdir(keyfoldername)
    else:
        os.remove(keyfoldername)


def recvmove(s, keyfoldername):
    recvcreate(s, keyfoldername)
    recvdelete(s, keyfoldername)


def senddelete(s, src):
    s.send(os.sep.encode() + b'\n')
    s.send(src.encode('utf-8') + b'\n')


def sendmove(s, src, dst):
    pass


# senddelete(s, keyfoldername, src)
# sendcreate(s, keyfoldername, dst)


def sendcreate(s, keyfoldername, src):
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


# s.send('modify'.encode('utf-8') + b'\n')
# return sendcreate(s, directory, src)


def eventrecieved(option, s, foldername, mapkeyofmapclientandchanges=None, clientid=0):
    if option == 'create':
        return recvcreate(s, foldername, True, os.sep, mapkeyofmapclientandchanges, clientid)
    if option == 'delete':
        return recvdelete(s, mapkeyofmapclientandchanges)
    if option == 'move':
        return recvmove(s.mapkeyofmapclientandchanges)
    if option == 'modify':
        return recvcreate(s, foldername, mapkeyofmapclientandchanges)
