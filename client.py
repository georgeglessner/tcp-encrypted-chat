import select, socket, sys

def main():
    s = socket.socket()
    ip_addr = raw_input("Enter an IP Adrress: ")
    port = input("Enter a Port Number: ")
    username = raw_input("Enter a Username: ")

    s.connect((ip_addr,port))
    s.send(username)
    s.setblocking(0)
    inout = [sys.stdin,s]

    print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    print "CHAT"
    print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
     
    running = 1
    while(running):
        readable,writable,exeptional = select.select(inout,[],[])
        for sock in readable:
            if sock == s:
                data = sock.recv(1024)
                if not data:
                    sys.exit()
                else:
                    print data
            else:
                msg = raw_input()
                s.send(msg)
    s.close()

if __name__ == "__main__":
    main()