#!/usr/bin/env python3

from __future__ import absolute_import, division, print_function, unicode_literals
import socket
import pika
import uuid
import pickle
import json
import bluetooth
from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf
import traceback

if __name__ == '__main__':
    ##### Bluetooth Setup ############
    port = 3
    backlog = 1
    size = 1024
    s = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

    s.bind(('', port))
    s.listen(backlog)
    ##### END OF Bluetooth Setup #####

    ##### Time to obtain the Repo RPi's IP Address using zeroconf #####
    zeroconf = Zeroconf()
    print("\n\n\nBrowsing services, press Ctrl-C to exit...")

    # Info contains the server information we will be looking for to set up zeroconf
    info = zeroconf.get_service_info("_amqp._tcp.local.", "rabbitmq._amqp._tcp.local.")

    # If we can't find the server then the assert statement will end the program
    assert info

    # The whole reason of using zeroconf. We are able to obtain the repo RPi's
    # IP address simply by broadcasting service info from the repo RPi.
    address = str(socket.inet_ntoa(info.address))

    #Testing purposes.
    print("Repo IP Address: " + address)
    ####################################################################

    # We will use the BridgeMQ class to set up the RabbitMQ server between bridge and repo
    class BridgeMQ(object):
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
            return self.response

    # Create an instance of the BridgeMQ class for our use
    bridge_rpc = BridgeMQ()

    print("Requesting Response from Repo over RabbitMQ")

    ##### Meat and Potatoes ###########
    try:
        client, clientInfo = s.accept()
        print("Bluetooth Server Started!")
        while 1:
            data = client.recv(size)
            if data:
                print("Bluetooth Data Received!")

                #Unpickle the data from BD client
                sendMe = pickle.loads(data)

                #Serialize the data with json
                sendMe = json.dumps(sendMe)

                #Make an RPC call to repo
                response = json.loads( bridge_rpc.call(sendMe).decode("utf-8") )

                #Send response (from repo) to client
                client.send(pickle.dumps(response))
                print("Sent Repo Reponse to Client")

    except Exception:
        #print("Exception raised: " + traceback.format_exc())
        print("Closing socket")
        client.close()
        s.close()
    ##### End of Meat and Potatoes #####

    zeroconf.close()
