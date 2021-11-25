import os

chunk = 1000000


# send all the back-up folder to the socket
def send_all(s, key_folder_name):
    with s:
        s.send(os.sep.encode() + b'\n')
        for path, dirs, files in os.walk(key_folder_name):
            for d in dirs:
                send_folder(s, os.path.join(path, d), key_folder_name)
            for file1 in files:
                sendfile(s, key_folder_name, os.path.join(path, file1))
    print('Done')


# receive all the changes in the back-up folder from the socket
def receive_changes(sock, folder_name, size, map_key_of_map_client_and_changes=None, computer_id=0):
    while size > 0:
        try:
            rec = readline(sock)
            if not rec:
                break
            change = rec.strip()
            receive_event(change, sock, folder_name, map_key_of_map_client_and_changes, computer_id)
            size = size - 1
        except:
            break


# receive all the back-up folder from the socket
def receive_folders(sock, folder_name):
    count = 0
    with sock:
        while True:
            if count == 0:
                flag = receive_create(sock, folder_name, True)
                count = 1
            else:
                flag = receive_create(sock, folder_name, False)
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
def receive_create(s, key_folder_name, map_key_of_map_client_and_changes=None, computer_id=0):
    filename, path, length = receive(s, key_folder_name, map_key_of_map_client_and_changes, 'created', computer_id)

    if filename[0] == 'd':
        os.makedirs(path, exist_ok=True)
        print('Complete')
        return 1
    os.makedirs(os.path.dirname(path), exist_ok=True)

    return write_file(s, path, length)


# write a file
def write_file(s, path, length):
    with open(path, 'wb') as f:
        while length:
            # Read the data in chunks so it can handle large files.
            chunk_data = min(length, chunk)
            data = s.recv(chunk_data)
            if not data:
                break
            f.write(data)
            length -= len(data)
        else:  # only runs if while doesn't break and length==0
            print('Complete')
            return 1
    return -1


# send a folder
def send_folder(s, path, key_folder_name):
    rel_path_dir = os.path.relpath(path, key_folder_name)
    dir_size = 0
    print(f'Sending {rel_path_dir}')
    s.send(b'd' + rel_path_dir.encode('utf-8') + b'\n')
    s.send(str(dir_size).encode('utf-8') + b'\n')


# send a file
def sendfile(s, key_folder_name, filename):
    rel_path = os.path.relpath(filename, key_folder_name)
    filesize = os.path.getsize(filename)
    print(f'Sending {rel_path}')

    with open(filename, 'rb') as f:
        s.send(b'f' + rel_path.encode('utf-8') + b'\n')
        s.send(str(filesize).encode('utf-8') + b'\n')

        # Send the file in chunks so large files can be handled.
        data = f.read(chunk)
        while data:
            s.send(data)
            data = f.read(chunk)


# receive files
def receive(s, key_folder_name, map_key_of_map_client_and_changes, change, computer_id=0):
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
                    map_key_of_map_client_and_changes[key_folder_name][cid].append((path, '', change))
                else:
                    map_key_of_map_client_and_changes[key_folder_name][cid] = [(path, '', change)]
    print(f'Downloading {path}...\n  Expecting {length:,} bytes...', end='', flush=True)
    return filename, path, length


# receive a file modified
def receive_file(s, key_folder_name, map_key_of_map_client_and_changes=None, computer_id=0):
    filename, path, length = receive(s, key_folder_name, map_key_of_map_client_and_changes, 'modified', computer_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_file(s, path, length)


# receive a report about a delete in the client's folder
def receive_delete(s, key_folder_name, map_key_of_map_client_and_changes=None, computer_id=0):
    separator = readline(s)
    path = readline(s)
    all_path = key_folder_name
    for name in path.split(separator):
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
def receive_move(s, key_folder_name, map_key_of_map_client_and_changes, computer_id):
    separator = readline(s)

    # define the path of the source
    src = readline(s)
    for d in src.split(separator)[1:]:
        key_folder_name = os.path.join(key_folder_name, d)
    src = key_folder_name
    key_folder_name = key_folder_name.split(separator)[0]

    # define the path of the destination
    dst = readline(s)
    for d in dst.split(separator)[1:]:
        key_folder_name = os.path.join(key_folder_name, d)
    dst = key_folder_name
    key_folder_name = key_folder_name.split(separator)[0]

    # add the change to every computer of the client
    if map_key_of_map_client_and_changes is not None:
        for cid in map_key_of_map_client_and_changes[key_folder_name].keys():
            if cid != computer_id:
                if map_key_of_map_client_and_changes[key_folder_name][cid] is not None:
                    map_key_of_map_client_and_changes[key_folder_name][cid].append((src, dst, 'moved'))
                else:
                    map_key_of_map_client_and_changes[key_folder_name][cid] = [(src, dst, 'moved')]
    print(f'Moving')

    os.rename(src, dst)


# send about a file deleted
def send_delete(s, src):
    s.send('delete'.encode('utf-8') + b'\n')
    s.send(os.sep.encode() + b'\n')
    s.send(src.encode('utf-8') + b'\n')


# send about a file moved
def send_move(s, src, dst):
    s.send('move'.encode('utf-8') + b'\n')
    s.send(os.sep.encode() + b'\n')
    s.send(src.encode('utf-8') + b'\n')
    s.send(dst.encode('utf-8') + b'\n')


# send about a new file created
def send_create(s, key_folder_name, src):
    s.send('create'.encode('utf-8') + b'\n')
    s.send(os.sep.encode() + b'\n')
    if os.path.isdir(src):
        send_folder(s, src, key_folder_name)
    else:
        sendfile(s, key_folder_name, src)


# call the function according to the report we want to send
def send_event(option, s, directory, src, dst):
    if option == 'created':
        return send_create(s, directory, src)
    if option == 'deleted':
        return send_delete(s, os.path.relpath(src, directory))
    if option == 'moved':
        return send_move(s, src, dst)
    if option == 'modified':
        s.send('modify'.encode('utf-8') + b'\n')
        s.send(os.sep.encode() + b'\n')
        return sendfile(s, directory, src)


# call the function according to the report we got
def receive_event(option, s, folder_name, map_key_of_map_client_and_changes=None, computer_id=0):
    if option == 'create':
        return receive_create(s, folder_name, True, os.sep, map_key_of_map_client_and_changes, computer_id)
    if option == 'delete':
        return receive_delete(s, folder_name, map_key_of_map_client_and_changes, computer_id)
    if option == 'move':
        return receive_move(s, folder_name, map_key_of_map_client_and_changes, computer_id)
    if option == 'modify':
        return receive_file(s, folder_name, map_key_of_map_client_and_changes, computer_id)
