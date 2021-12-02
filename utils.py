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


# receive all the changes in the back-up folder from the socket
def receive_changes(s, folder_name, size, map_changes=None, computer_id=0, event_list_before_receive=None):
    while size > 0:
        receive_event(readline(s).strip(), s, folder_name, map_changes, computer_id, event_list_before_receive)
        size = size - 1


# receive all the back-up folder from the socket
def receive_folders(s, folder_name):
    separator = readline(s)
    while True:
        if receive_create(s, folder_name, separator) == -1:
            break


# read a line from the socket
def readline(s):
    rec = s.recv(1).decode()
    while '\n' not in rec and rec:
        rec += s.recv(1).decode()
    if rec:
        return rec[:-1]
    return ''


# receive a report about a new file in the client's folder
def receive_create(s, key_folder_name, separator, map_changes=None, computer_id=0, event_list_before_receive=None):
    rec = readline(s)
    if not rec:
        return -1

    # get the name, the length and the path of the file
    filename = rec[1:].strip()
    length = int(readline(s))
    path = key_folder_name
    for dirname in filename.split(separator):
        path = os.path.join(path, dirname)

    # send all the computers of the client the changes and to the event list before changes
    send_client_computers(map_changes, key_folder_name, computer_id, path, '', 'created')
    add_to_event_list_before_receive(event_list_before_receive, path, '', 'created')

    # create the directory or the new file
    if rec[0] == 'd':
        os.makedirs(path, exist_ok=True)
        return 1
    os.makedirs(os.path.dirname(path), exist_ok=True)

    return write_file(s, path, length)


# send a folder
def send_folder(s, path, key_folder_name):
    rel_path_dir = os.path.relpath(path, key_folder_name)
    dir_size = 0
    s.send(b'd' + rel_path_dir.encode() + b'\n')
    s.send(str(dir_size).encode() + b'\n')


# send a file
def sendfile(s, key_folder_name, filename):
    rel_path = os.path.relpath(filename, key_folder_name)
    filesize = os.path.getsize(filename)

    with open(filename, 'rb') as f:
        s.send(b'f' + rel_path.encode() + b'\n')
        s.send(str(filesize).encode() + b'\n')

        # Send the file in chunks so large files can be handled.
        data = f.read(chunk)
        while data:
            s.send(data)
            data = f.read(chunk)


# send all the computers the change in the back-up folder
def send_client_computers(map_key_of_map_client_and_changes, key_folder_name, computer_id, src, dst, report):
    if map_key_of_map_client_and_changes is not None:
        for cid in map_key_of_map_client_and_changes[key_folder_name].keys():
            if cid != computer_id:
                if map_key_of_map_client_and_changes[key_folder_name][cid] is not None:
                    map_key_of_map_client_and_changes[key_folder_name][cid].append((src, dst, report))
                else:
                    map_key_of_map_client_and_changes[key_folder_name][cid] = [(src, dst, report)]


# add the events from the server to the event list before changes
def add_to_event_list_before_receive(event_list_before_receive, src, dst, report):
    if event_list_before_receive is not None:
        event_list_before_receive.append((src, dst, report))


# write a file from the socket in the path
def write_file(s, path, length):
    # Read the data in chunks so it can handle large files.
    with open(path, 'wb') as f:
        while length:
            chunk_data = min(length, chunk)
            data = s.recv(chunk_data)
            if not data:
                break
            f.write(data)
            length -= len(data)
        else:  # only runs if while doesn't break and length==0
            return 1
    return -1


# remove directory recursively
def remove_directory(directory):
    for path, dirs, files in os.walk(directory):
        for f in files:
            os.remove(os.path.join(path, f))
        for d in dirs:
            remove_directory(os.path.join(path, d))
    os.rmdir(directory)
    

# receive a report about a delete in the client's folder
def receive_delete(s, key_folder_name, separator, map_key_of_map_client_and_changes=None, computer_id=0,
                   event_list_before_receive=None):
    path = readline(s)
    full_path = key_folder_name
    for name in path.split(separator):
        if name != '..' and name != '.':
            full_path = os.path.join(full_path, name)

    # delete the directory or the file
    if os.path.isdir(full_path):
        remove_directory(full_path)
    else:
        os.remove(full_path)
    send_client_computers(map_key_of_map_client_and_changes, key_folder_name, computer_id, full_path, '', 'deleted')

    # send all the computers of the client the changes and to the event list before changes
    add_to_event_list_before_receive(event_list_before_receive, full_path, '', 'deleted')


# receive a report about a move in the client's folder
def receive_move(s, key_folder_name, separator, map_key_of_map_client_and_changes, computer_id,
                 event_list_before_receive=None):
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

    # send all the computers of the client the changes and to the event list before changes
    send_client_computers(map_key_of_map_client_and_changes, key_folder_name, computer_id, src, dst, 'moved')
    add_to_event_list_before_receive(event_list_before_receive, src, dst, 'moved')

    # move the file by rename it
    os.rename(src, dst)


# send about a file deleted
def send_delete(s, src):
    s.send('delete'.encode() + b'\n')
    s.send(os.sep.encode() + b'\n')
    s.send(src.encode() + b'\n')


# send about a file moved
def send_move(s, src, dst):
    s.send('move'.encode() + b'\n')
    s.send(os.sep.encode() + b'\n')
    s.send(src.encode() + b'\n')
    s.send(dst.encode() + b'\n')


# send about a new file created
def send_create(s, key_folder_name, src):
    s.send('create'.encode() + b'\n')
    s.send(os.sep.encode() + b'\n')
    if os.path.isdir(src):
        send_folder(s, src, key_folder_name)
    else:
        sendfile(s, key_folder_name, src)


# call the function according to the report we want to send
def send_event(option, s, directory, src, dst):
    if option == 'created':
        send_create(s, directory, src)
    if option == 'deleted':
        send_delete(s, os.path.relpath(src, directory))
    if option == 'moved':
        send_move(s, src, dst)
    if option == 'modified':
        s.send('modify'.encode() + b'\n')
        s.send(os.sep.encode() + b'\n')
        sendfile(s, directory, src)


# call the function according to the report we got
def receive_event(option, s, folder_name, map_changes=None, computer_id=0,
                  events_before_receive=None):
    separator = readline(s)
    if option == 'create':
        return receive_create(s, folder_name, separator, map_changes, computer_id, events_before_receive)
    if option == 'delete':
        return receive_delete(s, folder_name, separator, map_changes, computer_id, events_before_receive)
    if option == 'move':
        return receive_move(s, folder_name, separator, map_changes, computer_id, events_before_receive)
    if option == 'modify':
        return receive_create(s, folder_name, separator, map_changes, computer_id, events_before_receive)
