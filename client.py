#!/usr/bin/env python

import select
import socket
import sys
import random

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.fernet import Fernet

ADMIN_PWD = 'pwd'

def main():
    # Read public key from file and convert it to public_key type
    file = open("public_key.pem", "r")
    pub_key_data = file.read()
    pub_key = load_pem_public_key(pub_key_data, backend=default_backend())
    
    # Generate symmetric key
    fernet_key = Fernet.generate_key()
    print fernet_key

    # RSA encrypt the symmetric key
    encrypted_pub_key = pub_key.encrypt(
        fernet_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # establish connection with chat server
    s = socket.socket()
    ip_addr = raw_input('Enter an IP Adrress: ')
    port = input('Enter a Port Number: ')
    s.connect((ip_addr, port))
    s.send(encrypted_pub_key)
    data = s.recv(1024)
    print data
    running = 1
    while running:
        username = raw_input('Enter a Username: ')
        s.send(username)
        data = s.recv(1024)
        print data
        if data != 'Username already taken... Please use another.':
            break

    s.setblocking(0)
    inout = [sys.stdin, s]

    print '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
    print 'CHAT'
    print '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'


    while(running):
        readable, writable, exeptional = select.select(inout, [], [])
        for sock in readable:
            if sock == s:
                data = sock.recv(1024)
                if data == 'close_socket':
                    s.close()
                    sys.exit()
                elif not data:
                    sys.exit()
                else:
                    print data
            else:
                msg = raw_input()
                if msg == 'quit':
                    final_msg = username + ': ' + msg
                    s.send(final_msg)
                elif msg[0:5] == '$boot':
                    admin = raw_input('Enter password: ')
                    if admin == ADMIN_PWD:
                        final_msg = username + ': ' + msg
                        s.send(final_msg)
                    else:
                        print 'Invalid Password!'
                else:
                    final_msg = username + ': ' + msg
                    s.send(final_msg)

if __name__ == '__main__':
    main()
