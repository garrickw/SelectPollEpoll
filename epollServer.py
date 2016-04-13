""" An example about how to use linux epoll in python """
import socket
import select
from wsgiref.handlers import format_date_time
from time import time

EOLS = [b'\n\n', b'\n\r\n']

# make http response
response = b'HTTP/1.0 200 OK\r\nDate:{}\r\n'.format(format_date_time(time()))
response += b'Content-Type: text/plain\r\nContent-Length: 13\r\n\r\n'
response += b'Hello, world!'

# make socket
server_addr = ('localhost', 8888)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(server_addr)
sock.setblocking(0)
sock.listen(1024)

# create an epoll object
epoll = select.epoll()
# set edge_trigger
epoll.register(sock.fileno(), select.EPOLLIN | select.EPOLLET)


try:
    connections = {}
    requests = {}
    responses = {}
    addr = {}

    while True:
        events = epoll.poll(1)  # 1s timeout
        for fileno, event in events:
            # new connection
            if fileno == sock.fileno():
                try:
                    while True:
                        conn, client_addr = sock.accept()
                        print "A new connection is coming...", client_addr
                        conn.setblocking(0)
                        epoll.register(conn.fileno(), select.EPOLLIN)
                        addr[conn.fileno()] = client_addr
                        connections[conn.fileno()] = conn
                        requests[conn.fileno()] = b''
                        responses[conn.fileno()] = response
                except socket.error, e:
                    # because of non-blocking, accept will return error immediately
                    # when no connection comes
                    print "accept fail"
                    pass

            elif event & select.EPOLLIN:
                try:
                    while True:
                        data = connections[fileno].recv(1024)
                        if data:
                            requests[fileno] += data
                        elif not requests[fileno]:
                            epoll.modify(fileno, 0)
                            connections[fileno].shutdown(socket.SHUT_RDWR)
                            break

                        # check wether all datas were received or not
                        if any([eol in data for eol in EOLS]):
                            epoll.modify(fileno, select.EPOLLOUT)
                            print('-'*79 + '\n' + requests[fileno].decode()[:-2])
                except socket.error:
                    print "error in"
                    pass

            elif event & select.EPOLLOUT:
                try:
                    while True:
                        byteswritten = connections[fileno].send(responses[fileno])
                        responses[fileno] = responses[fileno][byteswritten:]
                        if len(responses[fileno]) == 0:
                            epoll.modify(fileno, 0)
                            connections[fileno].shutdown(socket.SHUT_RDWR)
                except socket.error:
                    print "error out"
                    pass

            elif event & select.EPOLLHUP:
                print fileno
                epoll.unregister(fileno)
                o += 1
                connections[fileno].close()
                del connections[fileno]
                del responses[fileno]
finally:
    epoll.unregister(sock.fileno())
    epoll.close()
    sock.close()
