import select, socket, sys, Queue

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setblocking(0)
    server.bind(('localhost', 1234))
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
                # 'Show Clients' command
                if data == '$show_clients':
                    data = ""
                    data += "CLIENT LIST: " + ", ".join(client_list)
                if data:
                    # 'Broadcast' command
                    if data == "$broadcast":
                        count = 0
                        for client in inputs:
                            if count == 0:
                                count+=1
                            else: 
                                message_queues[client].put(data)
                                outputs.append(client)
                                count+=1
                    elif s not in outputs:
                        message_queues[s].put(data)
                        outputs.append(s) 
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