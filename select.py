"""An example about how to use python's select.select"""

import select
import socket
import sys
import Queue

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setblocking(0)  # set socket non-blocking
server_address = ('localhost', 8888)
server.bind(server_address)
server.listen(5)

# Sockets from which we expect to read
inputs = [server]

# Sockets to which we expect to write
outputs = []

# Outgoing message queues (socket:Queue)
message_queues = {}

while inputs:
    print "new select begins......"
    timeout = 5
    readable, writable, exceptional = select.select(inputs, outputs, inputs, timeout)
    # timeout
    if not (readable or writable or exceptional):
        print "select timeout."
        continue

    for sock in readable:
        if sock is server:   # new connection comes
            connection, client_address = sock.accept()
            print "new connection({})".format(client_address)
            connection.setblocking(0)
            inputs.append(connection)
            # set a queue for the new one
            message_queues[connection] = Queue.Queue()

        else:
            data = sock.recv(1024)
            if data:
                print 'received "{}" from {}'.format(data, sock.getpeername())
                # send back the same data by adding it into the queue
                message_queues[sock].put(data)
                if sock not in outputs:
                    outputs.append(sock)

            else:  # no data, means it is time to close
                print "{} is closing.".format(client_address)
                if sock in outputs:
                    outputs.remove(sock)
                    sock.close()
                    del message_queues[sock]

    for sock in writable:
        try:
            next_message = message_queues[sock].get_nowait()
        except Queue.Empty:
            print "the output queue is empty"
            outputs.remove(sock)
        else:
            print "sending '{}' to '{}'".format(next_message, sock.getpeername())
            sock.send(next_message)

    # hendle the exception
    for sock in exceptional:
        print "handling the exception"
        inputs.remove(sock)
        if sock in outputs:
            outputs.remove(sock)
        sock.close()
        del message_queues[sock]
