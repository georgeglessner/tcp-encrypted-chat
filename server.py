#!/usr/bin/env python

import select
import socket
import sys
import Queue

def broadcast_msg(command):
    temp = command.split()
    temp[1] = temp[1].replace(temp[1][0], '[')
    temp[1] = temp[1] + ']'
    swap_temp = temp[1]
    temp[1] = temp[0]
    temp[0] = swap_temp
    return ' '.join(temp)


def main():
    global server
    ip_addr = int(raw_input('Enter a Port Number: '))
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setblocking(0)
    server.bind(('localhost', ip_addr))
    server.listen(5)
    inputs = [server]
    outputs = []
    message_queues = {}
    username_flag = 1
    client_list = []

    print 'Server Running...'

    while inputs:
        readable, writable, exceptional = select.select(
            inputs, outputs, inputs)
        for s in readable:
            if s is server:
                connection, client_address = s.accept()
                connection.setblocking(0)
                print connection
                inputs.append(connection)
                message_queues[connection] = Queue.Queue()
                username_flag = 1
            else:
                data = s.recv(1024)
                # don't print if client disconnects
                if data == '':
                    pass
                else:
                    print 'Received from', str(data)
                    if username_flag:
                        if data in client_list:
                            temp = 'Username already taken... Please use another.'
                            username_flag = 1
                            message_queues[s].put(temp)
                            outputs.append(s)
                            break
                        else:
                            client_list.append(data)
                            temp = 'Valid username... Connecting to chat.'
                            username_flag = 0
                            message_queues[s].put(temp)
                            outputs.append(s)
                            break
                    if data:
                        is_quit = data.split(': ')
                        if is_quit[1] == 'quit':
                            if is_quit[0] in client_list:
                                recipient = client_list.index(is_quit[0])
                                client_list.pop(recipient)
                                temp_data = 'close_socket'
                                recipient += 1
                                message_queues[inputs[recipient]].put(temp_data)
                                outputs.append(inputs[recipient])
                                recipient = inputs.index(s)
                                inputs.pop(recipient)
                        # If data is a command
                        temp = data.split()
                        if temp[1][0] == '$':
                            # get client list
                            if temp[1] == '$clients':
                                data = ''
                                data += 'CLIENT LIST: ' + \
                                    ', '.join(client_list)
                            # send broadcast message
                            if temp[1] == '$broadcast':
                                count = 0
                                for client in inputs:
                                    if count == 0:
                                        count += 1
                                    else:
                                        message_queues[client].put(
                                            broadcast_msg(data))
                                        outputs.append(client)
                                        count += 1
                            if temp[1] == '$boot':
                                if temp[2] in client_list:
                                    recipient = client_list.index(temp[2])
                                    client_list.pop(recipient)
                                    temp_data = 'close_socket'
                                    message_queues[inputs[recipient]].put(
                                        temp_data)
                                    outputs.append(inputs[recipient])
                                else:
                                    data = 'Client not in list'
                            # Invalid command
                            if temp[1] == 'Invalid command':
                                data = 'Invalid Command'
                        # message to client
                        temp_data = data.split()
                        # send to specific client
                        if temp_data[1] == '$sendto':
                            if temp_data[2] in client_list:
                                recipient = client_list.index(temp_data[2])
                                recipient += 1
                                temp_data = temp_data[0] + \
                                    ' '.join(temp_data[3:])
                                message_queues[inputs[recipient]].put(
                                    temp_data)
                                outputs.append(inputs[recipient])
                            else:
                                data = 'Client not in list'
                        # Echo message
                        elif s not in outputs:
                            message_queues[s].put(data)
                            outputs.append(s)
                    # Client Disconnected
                    else:
                        if s in outputs:
                            outputs.remove(s)
                            client
                        inputs.remove(s)
                        s.close()
                        del message_queues[s]

        for s in writable:
            try:
                next_msg = message_queues[s].get_nowait()
            except Queue.Empty:
                outputs.remove(s)
            else:
                s.send(next_msg)
                print 'Sent-> ' + next_msg

        for s in exceptional:
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()
            del message_queues[s]


if __name__ == '__main__':
    main()
