import socket
import sys
import time
import os
from utils import send_all, receive_folders, send_event, readline, receive_changes
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

chunk = 1000000
event_list = list()
last_event = None
event_list_before_receive = list()


def is_relevant(event):
    for e in event_list_before_receive:
        print(e[0])
        print(event.src_path)
        if e[0] in event.src_path or e[0] in event.dest_path or e[1] in event.src_path or e[1] in event.dest_path:
            return False
    return True


# notify about creating a new file in the back-up folder
def on_created(event):
    if ('.goutputstream' not in event.src_path) and ('.swp' not in event.src_path):
        #if (last_event is not None) and (last_event[0] == event.src_path) and (last_event[2] == 'created'):
        #    return
        event_list.append((event.src_path, '', 'created'))
        #last_event = (event.src_path, '', 'created')
        print(f"Someone created {event.src_path}!")


# notify about deleting a file in the back-up folder
def on_deleted(event):
    if ('.goutputstream' not in event.src_path) and ('.swp' not in event.src_path):
        #if (last_event is not None) and (last_event[0] == event.src_path) and (last_event[2] == 'deleted'):
        #    return
        for e in reversed(event_list):
            if e[2] == 'modified' and e[0] == event.src_path:
                event_list.remove(e)
            if e[2] == 'created' and e[0] == event.src_path:
                event_list.remove(e)
                return
        event_list.append((event.src_path, '', 'deleted'))
        #last_event = (event.src_path, '', 'deleted')
        print(f"Someone deleted {event.src_path}!")


# notify about modify a file in the back-up folder
def on_modified(event):
    if (not os.path.isdir(event.src_path)) and ('.goutputstream' not in event.src_path) \
            and ('.swp' not in event.src_path):
        event_list.append((event.src_path, '', 'modified'))
        #last_event = (event.src_path, '', 'modified')
        print(f"hey, {event.src_path} has been modified")


# notify about move a file in the back-up folder
def on_moved(event):
    #if is_relevant(event):
        if '.goutputstream' in event.src_path:
            event_list.append((event.dest_path, '', 'modified'))
            #last_event = (event.dest_path, '', 'modified')
            print(f"hey, {event.dest_path} has been modified")
        else:
            #if (last_event is not None) and ((last_event[0] + os.path.sep) in event.src_path) and (last_event[2] == 'moved'):
            #    print(f"not added moved {event.src_path} to {event.dest_path}")
            #    return
            #if (last_event is not None) and (last_event[0] == event.src_path) and (last_event[1] == event.dest_path) and\
            #        (last_event[2] == 'moved'):
            #    return
            length = len(event_list)
            for i in range(length):
                if event_list[length - i - 1][2] == 'modified' and event_list[length - i - 1][0] == event.src_path:
                    l = list(event_list[length - i - 1])
                    l[0] = event.dest_path
                    event_list[length - i - 1] = tuple(l)

                if event_list[length - i - 1][2] == 'created' and event_list[length - i - 1][0] == event.src_path:
                    l = list(event_list[length - i - 1])
                    l[0] = event.dest_path
                    event_list[length - i - 1] = tuple(l)
                    return
            event_list.append((event.src_path, event.dest_path, 'moved'))
            #last_event = (event.src_path, event.dest_path, 'moved')
            print(f"someone moved {event.src_path} to {event.dest_path}")


# connect the computer in the first time to the server of an existing client
def first_connection_new_computer(s, arguments):
    key = arguments[5]
    s.send(b'n' + key.encode())
    try:
        computer_id = s.recv(7).decode()
        receive_folders(s, arguments[3])
    except:
        computer_id = ''
        print("receive folders failed")
    return key, computer_id


# connect the client in the first time to the server
def first_connection_new_client(s, arguments):
    s.send('Hi'.encode())
    computer_id = s.recv(7).decode()
    key = s.recv(128).decode()
    with open("key_file", 'wb') as f:
        f.write(key.encode())
    if not os.path.isdir(arguments[3]):
        os.makedirs(arguments[3], exist_ok=True)
    try:
        send_all(s, arguments[3])
    except:
        print("send folders failed")
    return key, computer_id


# get new socket for the client
def get_socket(ip, port, time_sleep):
    sc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sc.connect((ip, int(port)))
    #sc.settimeout(int(time_sleep))
    #if int(time_sleep) < 5:
    #    sc.settimeout(5)
    return sc


if __name__ == "__main__":

    # get the arguments of the client
    ip = sys.argv[1]
    port = sys.argv[2]
    directory = sys.argv[3]
    time_sleep = sys.argv[4]

    s = get_socket(ip, port, time_sleep)

    # connect the client to the server
    if len(sys.argv) > 5:
        key, computer_id = first_connection_new_computer(s, sys.argv)
    else:
        key, computer_id = first_connection_new_client(s, sys.argv)

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
    event_list_before_receive = list()
    try:
        while True:

            # disconnect the client and go to sleep
            s.close()
            time.sleep(int(time_sleep))
            s = get_socket(ip, port, time_sleep)
            print("connected")
            event_list_before_receive = list()

            try:
                # connect the client again
                s.send(b'o' + key.encode())
                s.send(computer_id.encode())
                option = readline(s)
            except:
                pass

            # get new update from the server
            if option == 'updates from another computer':
                my_observer.stop()

                event_list_before_receive = list()
                try:
                    size = int(readline(s))
                    #receive_changes(s, directory, size, None, 0, event_list_before_receive)
                    receive_changes(s, directory, size)
                except:
                    print("receive changes failed")
                #print(event_list)

                # define an observer for the changes in the back-up directory of the client
                my_observer = Observer()
                my_observer.schedule(my_event, directory, recursive=True)
                my_observer.start()
            print("event_list")
            print(event_list)
            print("event_list_before_receive")
            print(event_list_before_receive)
            #event_list_before_receive_copy = event_list_before_receive.copy()
            #event_list_copy = event_list.copy()
            #for event_before in event_list_before_receive_copy:
            #    for event in event_list_copy:
            #        if event_before in event_list_before_receive and event in event_list and event_before[0] == event[0]:
            #            event_list = [value for value in event_list if value[0] != event_before[0]]
            #            event_list_before_receive.remove(event_before)

            # send new changes in the back-up folder of the client in this computer
            #print(event_list)
            try:
                s.send(str(len(event_list)).encode() + b'\n')
                copy_event_list = event_list.copy()
                for event in copy_event_list:
                    send_event(event[2], s, directory, event[0], event[1])
                    event_list.remove(event)
            except:
                pass

    except KeyboardInterrupt:
        my_observer.stop()
    my_observer.join()
