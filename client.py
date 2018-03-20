#!/usr/bin/env python

import select
import socket
import sys

ADMIN_PWD = 'pwd'

def main():
    s = socket.socket()
    ip_addr = raw_input('Enter an IP Adrress: ')
    port = input('Enter a Port Number: ')
    s.connect((ip_addr, port))
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
