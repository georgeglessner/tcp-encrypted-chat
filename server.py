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
from itertools import chain


def broadcast_msg(command, server):
    ''' Construct broadcast message '''
    global client_list

    for client in client_list:
        if client[1] == server:
            client = client[0]
    temp = command.split()
    temp[1] = temp[1].replace(temp[1][0], '[')
    temp[1] = temp[1] + ']'
    swap_temp = temp[1]
    temp[1] = temp[0]
    temp[0] = swap_temp
    data = ' '.join(temp)
    return data


def generate_keys():
    ''' Generate keys '''
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


def decrypt_symmetric_key(private_key, data):
    ''' Decrypt message with private key '''
    message = private_key.decrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return message


def encrypt_message(message, recipient):
    ''' Encrypt message to be sent to specified recipient '''
    global symmetric_key_list
    fernet_key = symmetric_key_list.get(recipient)
    f = Fernet(fernet_key)
    encrypted_message = f.encrypt(message)

    return encrypted_message


def main():
    global server, symmetric_key_list, client_list

    with open("private_key.pem", "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )

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
                    if symmetric_key_flag:
                        hold_symmetric_key = decrypt_symmetric_key(
                            private_key, data)
                        symmetric_key_flag = 0
                        temp = 'Established encrypted connection to server'
                        message_queues[s].put(temp)
                        outputs.append(s)
                        break
                    elif username_flag:
                        if data in chain.from_iterable(client_list):
                            temp = 'Username already taken... Please use another.'
                            username_flag = 1
                            message_queues[s].put(temp)
                            outputs.append(s)
                            break
                        else:
                            client_list.append([data, s])
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
                        client = client_list[client][0]
                        token = symmetric_key_list.get(client)

                        # Decrypts the symmetric key
                        f = Fernet(token)
                        message = f.decrypt(data)
                        data = message

                        is_quit = data.split(': ')
                        if is_quit[1] == 'quit':
                            if is_quit[0] in chain.from_iterable(client_list):
                                index = 0
                                for client in client_list:
                                    if client[0] == is_quit[0]:
                                        recipient = client[0]
                                        break
                                    else:
                                        index += 1
                                client_list.pop(index)
                                temp = 'close_socket'
                                index += 1
                                token = encrypt_message(temp, recipient)
                                message_queues[inputs[index]].put(
                                    token)
                                outputs.append(inputs[index])
                                index = inputs.index(s)
                                inputs.pop(index)
                        # If data is a command
                        temp = data.split()
                        if temp[1][0] == '$':
                            # get client list
                            if temp[1] == '$clients':
                                data = ''
                                temp_client_list = []
                                for client in client_list:
                                    temp_client_list.append(client[0])
                                data += 'CLIENT LIST: ' + \
                                    ', '.join(temp_client_list)
                                index = 0
                                for client in client_list:
                                    if client[1] == s:
                                        recipient = client[0]
                                        break
                                    else:
                                        index += 1
                                index += 1
                                token = encrypt_message(data, recipient)
                                message_queues[inputs[index]].put(
                                    token)
                                outputs.append(inputs[index])
                            # send broadcast message
                            if temp[1] == '$broadcast':
                                index = 0
                                for client in client_list:
                                    recipient = client[0]
                                    index += 1
                                    message = broadcast_msg(
                                        data, client)
                                    token = encrypt_message(
                                        message, recipient)
                                    message_queues[inputs[index]].put(
                                        token)
                                    outputs.append(inputs[index])
                            if temp[1] == '$boot':
                                if temp[2] in chain.from_iterable(client_list):
                                    index = 0
                                    for client in client_list:
                                        if client[0] == temp[2]:
                                            recipient = client[0]
                                            break
                                        else:
                                            index += 1
                                    temp = 'close_socket'
                                    client_list.pop(index)
                                    index += 1
                                    token = encrypt_message(temp, recipient)
                                    message_queues[inputs[index]].put(
                                        token)
                                    outputs.append(inputs[index])
                                    inputs.pop(index)
                                else:
                                    for client in client_list:
                                        if client[1] == s:
                                            client = client[0]
                                    data = 'Client not in list'
                                    data = encrypt_message(data, client)
                            # Invalid command
                            if temp[1] == 'Invalid command':
                                data = 'Invalid Command'
                        # message to client
                        # send to specific client
                        if temp[1] == '$sendto':
                            if temp[2] in chain.from_iterable(client_list):
                                index = 0
                                for client in client_list:
                                    if client[0] == temp[2]:
                                        recipient = client[0]
                                        break
                                    else:
                                        index += 1
                                index += 1
                                for client in client_list:
                                    if client[1] == s:
                                        client = client[0]
                                temp = temp[0] + \
                                    ' '.join(temp[3:])
                                token = encrypt_message(temp, recipient)
                                message_queues[inputs[index]].put(
                                    token)
                                outputs.append(inputs[index])
                            else:
                                for client in client_list:
                                    if client[1] == s:
                                        client = client[0]
                                data = 'Client not in list'
                                data = encrypt_message(data, client)

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
