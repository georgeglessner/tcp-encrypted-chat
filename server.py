#!/usr/bin/env python
import select
import socket
import sys
import Queue

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

def broadcast_msg(command):
    temp = command.split()
    temp[1] = temp[1].replace(temp[1][0], '[')
    temp[1] = temp[1] + ']'
    swap_temp = temp[1]
    temp[1] = temp[0]
    temp[0] = swap_temp
    return ' '.join(temp)

def generate_keys():
    # Private key generation
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    priv = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )

    priv.splitlines()[0]

    public_key = private_key.public_key()
    pub = public_key.public_bytes(
       encoding=serialization.Encoding.PEM,
       format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    pub.splitlines()[0]
    return 0

def decrypt_symmetric_key(private_key,data):
    plaintext = private_key.decrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    print plaintext
    return plaintext


def main():
    with open("private_key.pem", "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )


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
    symmetric_key_flag = 1
    client_list = []
    symmetric_key_list = {}

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
                symmetric_key_flag = 1
            else:
                data = s.recv(1024)
                # don't print if client disconnects
                if data == '':
                    pass
                else:
                    print 'Received from', str(data)
                    if symmetric_key_flag:
                        hold_symmetric_key = decrypt_symmetric_key(private_key,data)
                        symmetric_key_flag = 0
                        temp = 'Established encrypted connection to server'
                        message_queues[s].put(temp)
                        outputs.append(s)
                        break
                    elif username_flag:
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
                            symmetric_key_list[data] = hold_symmetric_key
                            break
                    if data:
                        # Gets the clients symmetric key
                        client = inputs.index(s)
                        client -= 1
                        client = client_list[client]
                        token = symmetric_key_list.get(client)

                        # Decrypts the symmetric key
                        f = Fernet(token)
                        plaintext = f.decrypt(data)
                        data = plaintext
                        
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
