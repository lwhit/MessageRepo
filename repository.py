#!/usr/bin/python3

import socket
import sys
import pika
import pymongo
import bluetooth
import pickle
import re
import json
import netifaces as ni

from pymongo import MongoClient
from zeroconf import ServiceInfo, Zeroconf

import RPi.GPIO as GPIO
import time

# ======================================
# Create datebase to send messsges to
# ======================================

output = ''
client = MongoClient('localhost', 27017)
db = client['test_database'] # Using the database provided by MongoDB
posts = db.posts

# ======================================
# GPIO Control
# ======================================
def gpioControl( count ):
    # pin 21 = blue, pin 20 = green, pin 16 = red
    GPIO.setmode( GPIO.BCM )
    GPIO.setwarnings(False)
    GPIO.setup(16, GPIO.OUT)
    GPIO.setup(20, GPIO.OUT)
    GPIO.setup(21, GPIO.OUT)

    GPIO.output(16, False)
    GPIO.output(20, False)
    GPIO.output(21, False)

    a = 0
    b = 0
    c = 0

    a = count % 10
    count = (count - a) / 10

    b = count % 10
    count = (count - b) / 10

    c = count

    time.sleep(1)
    # Red blink
    while (c != 0):
        GPIO.output(16, True)

        time.sleep(.25)
        GPIO.output(16, False)
        time.sleep(.25)
        c -= 1

    # Blue blink
    while (b != 0):
        GPIO.output(21, True)

        time.sleep(.25)
        GPIO.output(21, False)
        time.sleep(.25)
        b -= 1

    # Green blink
    while (a != 0):
        GPIO.output(20, True)

        time.sleep(.25)
        GPIO.output(20, False)
        time.sleep(.25)
        a -= 1

    GPIO.cleanup()
    return

# ======================================
# Initalize zeroconf
# Advertise rabbitMQ queue
# ======================================

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

# ======================================
# Access rabbitMQ shared queue
# ======================================

    connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))

    channel = connection.channel()

    channel.queue_declare(queue='myQueue')

    def on_request(ch, method, props, body):
        n = json.loads(body.decode("utf-8"))

        message = None
        subject = None

        if "Message" in n:
            message = n["Message"]

        if "Subject" in n:
            subject = n["Subject"]

        # ======================================
        # Access rabbitMQ shared queue
        # ======================================
        numPosts = posts.count() # Number of records in database
        if n["Action"] == 'push':
            post_id = posts.insert_one(n).inserted_id

            if posts.count() > numPosts:
                output = {"Status" : "Success"}

            else:
                output = {"Status" : "Fail"}

        elif n["Action"] == 'pull':
            output = []
            regmsg = re.compile("")
            regsub = re.compile("")

            if message is not None:
                regmsg = re.compile(message)

            if subject is not None:
                regsub = re.compile(subject)

            for post in posts.find():
                if regsub.search(str(post["Subject"])) is not None and regmsg.search(str(post["Message"])) is not None:
                    msg = {"MsgID" : post['MsgID'],
                           "Message" : post['Message']}

                    output.append(msg.copy())

            if len(output) == 0:
                output.append("Not Found")

        numPosts = posts.count() # Number of records in database
        # ===========================================================

        print("Received from Client: %s" % n)
        print("Number of Posts in Database: %d" % numPosts)
        gpioControl(numPosts)
        response = json.dumps(output)

        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id = \
                                                             props.correlation_id),
                         body=str(response))
        ch.basic_ack(delivery_tag = method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(on_request, queue='myQueue')

    print(" [x] Awaiting RPC requests")

# ======================================
#  Wait for messages from queue
# ======================================

    try:
        while True:
            channel.start_consuming()
            sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        print("Unregistering...")
        zeroconf.unregister_service(info)
        zeroconf.close()


