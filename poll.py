""" An example about how to use select.poll in python """

import select
import socket
import sys
import Queue

server_address = ('localhost', 8888)
TIMEOUT = 1000  # in millisecond

# create a socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# set non-blocking
server.setblocking(0)
print "server is starting on {}".format(server_address)
server.bind(server_address)
server.listen(5)

# set up a outgoing messages queue
message_queues = {}

# set flags
READ_ONLY = select.POLLIN | select.POLLPRI | select.POLLERR | select.POLLHUP
READ_WRITE = READ_ONLY | select.POLLOUT

# Since poll() returns a list of tuples containing the file descriptor and the event flag
# Map file descriptors to socket objects
fd_to_socket = { server.fileno(): server }

poller = select.poll()
#register server socket
poller.register(server, READ_ONLY)

while Ture:
    print "poll start......"
    events = poller.poll(TIMEOUT)

    for fd, flag in events:
        s = fd_to_socket[fd]

        # handle inputs
        if flag & (select.POLLPRI | select.POLLIN):
            if s is server: # new connection need to be accepted
                connection, client_address = s.accept()
                print "{} connected.".format(client_address)
                connection.setblocking(0)
                fd_to_socket[connection.fileno()] = s
                poller.register(s, READ_ONLY)
                message_queues[connection] = Queue.Queue()

            else:
                data = recv(1024)
                if data:
                    print "recieved data '{}' from '{}'".format(data, s.getpeername())
                    message_queues[s].push(data)
                    poller.modify(s, READ_WRITE)
                else:  #no data
                    print "{} close".format(s.getpeername())
                    del message_queues[s]
                    poller.unregister(s)
                    s.close()


        # The POLLHUP flag indicates a client that “hung up” the connection without closing it cleanly.                     
        elif flag & select.POLLHUP:
            # Client hung up
            print 'closing {} after receiving HUP'.format(s.getpeername())
            # Stop listening for input on the connection
            poller.unregister(s)
            s.close()

        elif flag & select.POLLOUT:
            try:
                next_msg = message_queues[s].get_nowait()
            except Queue.Empty:
                print "output queue for {} is Empty".format(s.getpeername())
                poller.modify(s, READ_ONLY)
            else:
                print "sending data '{}' to {}".format(next_msg, s.getpeername())
                s.send(next_msg)
        
        # handle error
        elif FLAG & select.POLLERR:
            print "handling exceptional condition for {}".format(s.getpeername())
            poller.unregister(s)
            s.close()
            del message_queues[s]
