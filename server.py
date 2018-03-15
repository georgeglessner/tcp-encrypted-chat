import select, socket, sys, Queue

def valid_commands(command):
    temp = command.split()
    if temp[0] == '$show_clients':
        return temp[0]
    elif temp[0] == '$broadcast':
        return temp[0]
    return 'Invalid command'

def broadcast_msg(command):
    temp = command.split()
    del temp[0]
    return " ".join(temp)
        

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setblocking(0)
    server.bind(('localhost', 12345))
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
                inputs.append(connection)
                message_queues[connection] = Queue.Queue()
                username_flag = 1
            else:
                data = s.recv(1024)
                print 'Recieved: ' + str(data)
                if username_flag:
                    client_list.append(data)
                    username_flag = 0
                    break
                if data:
                    # If data is a command
                    if data[0] == '$':
                        # 'Show Clients' command
                        if valid_commands(data) == '$show_clients':
                            data = ""
                            data += "CLIENT LIST: " + ", ".join(client_list)
                        # 'Broadcast' command
                        if valid_commands(data) == "$broadcast":
                            count = 0
                            for client in inputs:
                                if count == 0:
                                    count+=1
                                else: 
                                    message_queues[client].put(broadcast_msg(data))
                                    outputs.append(client)
                                    count+=1
                        # Invalid command
                        if valid_commands(data) == 'Invalid command':
                            data = 'Invalid Command'
                    # message to client
                    temp_data = data.split()
                    if temp_data[0] == 'to':
                        if temp_data[1] in client_list:
                            recipient = client_list.index(temp_data[1])
                            recipient += 1
                            temp_data = ' '.join(temp_data[2:])
                            print temp_data
                            message_queues[inputs[recipient]].put(temp_data)
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
                print 'Sent: ' + next_msg

        for s in exceptional:
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()
            del message_queues[s]

if __name__ == "__main__":
    main()