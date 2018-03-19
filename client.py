#!/usr/bin/env python

import select
import socket
import sys

ADMIN_PWD = 'pwd'

def main():
    s = socket.socket()
    ip_addr = raw_input('Enter an IP Adrress: ')
    port = input('Enter a Port Number: ')
    username = raw_input('Enter a Username: ')

    s.connect((ip_addr, port))
    s.send(username)
    s.setblocking(0)
    inout = [sys.stdin, s]

    print '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
    print 'CHAT'
    print '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'

    running = 1
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
                print msg[0:4]
                if msg[0:5] == '$boot':
                    admin = raw_input('Enter password: ')
                    if admin == ADMIN_PWD:
                        final_msg = username + ': ' + msg
                        s.send(final_msg)
                    else:
                        print 'Invalid Password!'
                else:
                    final_msg = username + ': ' + msg
                    s.send(final_msg)
    # s.close()


if __name__ == '__main__':
    main()
