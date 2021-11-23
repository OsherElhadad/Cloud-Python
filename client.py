import socket
import sys
import time
import os
from utils import sendfolders, recvfolders, eventhappenend, readline, recvchanges
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

chunk = 1000000
eventset = set()
observe = True


# notify about creating a new file in the back-up folder
def on_created(event):
    if observe:
        eventset.add((event.src_path, '', 'created'))
        print(f"Someone created {event.src_path}!")


# notify about deleting a file in the back-up folder
def on_deleted(event):
    if observe:
        eventset.add((event.src_path, '', 'deleted'))
        print(f"Someone deleted {event.src_path}!")


# notify about modify a file in the back-up folder
def on_modified(event):
    if observe:
        if not os.path.isdir(event.src_path):
            eventset.add((event.src_path, '', 'modified'))
            print(f"hey, {event.src_path} has been modified")


# notify about move a file in the back-up folder
def on_moved(event):
    if observe:
        eventset.add((event.src_path, event.dest_path, 'moved'))
        print(f"someone moved {event.src_path} to {event.dest_path}")


# connect the computer in the first time to the server of an existing client
def first_connection_new_computer(s, arguments):
    key = arguments[5]
    s.send(b'n' + key.encode('utf-8'))
    try:
        computer_id = s.recv(7).decode('utf-8')
        recvfolders(s, directory)
    except:
        print("receive folders failed")
    return key, computer_id


# connect the client in the first time to the server
def first_connection_new_client(s):
    s.send('Hi'.encode('utf-8'))
    computer_id = s.recv(7).decode('utf-8')
    key = s.recv(128).decode('utf-8')
    with open("key_file", 'wb') as f:
        f.write(key.encode('utf-8'))
    try:
        sendfolders(s, directory)
    except:
        print("send folders failed")
    return key, computer_id


# get new socket for the client
def get_socket(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, int(port)))
    s.settimeout(3)
    return s


if __name__ == "__main__":

    # get the arguments of the client
    ip = sys.argv[1]
    port = sys.argv[2]
    directory = sys.argv[3]
    time_sleep = sys.argv[4]

    # define the watchdog functions
    my_event = PatternMatchingEventHandler(["*"], None, False, True)
    my_event.on_created = on_created
    my_event.on_deleted = on_deleted
    my_event.on_modified = on_modified
    my_event.on_moved = on_moved

    # define an observer for the changes in the back-up directory of the client
    my_observer = Observer()
    my_observer.schedule(my_event, directory, recursive=True)
    my_observer.start()

    s = get_socket(ip, port)

    # connect the client to the server
    if len(sys.argv) > 5:
        key, computer_id = first_connection_new_computer(s, sys.argv)
    else:
        key, computer_id = first_connection_new_client(s)

    try:
        while True:

            # disconnect the client and go to sleep
            s.close()
            time.sleep(int(time_sleep))
            s = get_socket(ip, port)

            # connect the client again
            s.send(b'o' + key)
            s.send(computer_id.encode('utf-8'))
            option = readline(s)

            # get new update from the server
            if option == 'updates from another computer':
                run = False
                recvchanges(s, directory)
                run = True

            # send new changes in the back-up folder of the client in this computer
            s.send(str(len(eventset)).encode('utf-8') + b'\n')
            for event in eventset:
                eventhappenend(event[2], s, directory, event[0], event[1])
            eventset.clear()

    except KeyboardInterrupt:
        my_observer.stop()
    my_observer.join()
