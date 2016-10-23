#!/usr/bin/python3

import socket
import sys
from time import sleep
import pika
import netifaces as ni

from zeroconf import ServiceInfo, Zeroconf

if __name__ == '__main__':
    desc = {'queue_name': 'myQueue'}

    ni.ifaddresses('wlan0')
    ip = ni.ifaddresses('wlan0')[2][0]['addr']

    info = ServiceInfo("_amqp._tcp.local.",
                       "rabbitmq._amqp._tcp.local.",
                       socket.inet_aton(str(ip)), 5672, 0, 0,
                       desc, "rabbitmq-server.local.")

    zeroconf = Zeroconf()
    print("Registration of a service, press Ctrl-C to exit...")
    zeroconf.register_service(info)

# ===========================================

    connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))

    channel = connection.channel()

    channel.queue_declare(queue='myQueue')

    def fib(n):
        if n == 0:
            return 0
        elif n == 1:
            return 1
        else:
            return fib(n-1) + fib(n-2)

    def on_request(ch, method, props, body):
        n = int(body)

        print(" [.] fib(%s)" % n)
        response = fib(n)

        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id = \
                                                             props.correlation_id),
                         body=str(response))
        ch.basic_ack(delivery_tag = method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(on_request, queue='myQueue')

    print(" [x] Awaiting RPC requests")
    channel.start_consuming()

# ===========================================

    try:
        while True:
            sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        print("Unregistering...")
        zeroconf.unregister_service(info)
        zeroconf.close()


