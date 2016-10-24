#!/usr/bin/env python3
from __future__ import absolute_import, division, print_function, unicode_literals

""" Example of browsing for a service (in this case, HTTP) """

import socket
import sys
from time import sleep
import pika
import uuid

from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf

if __name__ == '__main__':
    zeroconf = Zeroconf()
    print("\nBrowsing services, press Ctrl-C to exit...\n")
    info = zeroconf.get_service_info("_amqp._tcp.local.", "rabbitmq._amqp._tcp.local.")
    assert info
#============================================================

    print("address: " + str(socket.inet_ntoa(info.address)))

    address = str(socket.inet_ntoa(info.address))

    class FibonacciRpcClient(object):
        def __init__(self):
            self.credentials = pika.PlainCredentials("pi", "asdf")
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(
                    host=address, credentials = self.credentials, socket_timeout = 2))

            self.channel = self.connection.channel()

            result = self.channel.queue_declare(exclusive=True)
            self.callback_queue = result.method.queue

            self.channel.basic_consume(self.on_response, no_ack=True,
                                       queue=self.callback_queue)

        def on_response(self, ch, method, props, body):
            if self.corr_id == props.correlation_id:
                self.response = body

        def call(self, n):
            self.response = None
            self.corr_id = str(uuid.uuid4())
            self.channel.basic_publish(exchange='',
                                       routing_key='myQueue',
                                       properties=pika.BasicProperties(
                                             reply_to = self.callback_queue,
                                             correlation_id = self.corr_id,
                                             ),
                                       body=str(n))
            while self.response is None:
                self.connection.process_data_events()
            return int(self.response)

    fibonacci_rpc = FibonacciRpcClient()

    print(" [x] Requesting fib(30)")
    response = fibonacci_rpc.call(30)
    print(" [.] Got %r" % response)

#============================================================

    zeroconf.close()
