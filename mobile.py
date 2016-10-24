#!usr/bin/env python3

import sys
import time
import argparse
import pymongo
import bluetooth
import pickle
import re

from pymongo import MongoClient

team = "12"

# Bluetooth information to connect to bridge pi
bd_addr = "B8:27:EB:F0:A7:D7"
port = 3
size = 1024

client = MongoClient('localhost', 27017)
db = client['test_database'] # Using the database provided by MongoDB
posts = db.posts
count = posts.count() # Number of records in database

parser = argparse.ArgumentParser()

# The first argument is required but subject/message arguments both aren't

parser.add_argument("-a", "--action", type = str,
                    required = True,
                    help = "push or pull messages")
parser.add_argument("-s", "--subject", type = str,
                    required = False,
                    help = "subject of the message")
parser.add_argument("-m", "--message", type = str,
                    required = False,
                    help = "message to be pusshed or pulled")

args = parser.parse_args()

action = args.action

subject = None
message = None

if args.subject:
    subject = args.subject

if args.message:
    message = args.message

# Checks to see at least one of the 2 is present
if subject is None and message is None:
    print("Must have at least the subject or a message, or both")
    exit()

# If the action is to push, there must be both arguments
if action == 'push':
    if subject is None:
        print("Must have subject")
        exit()

    elif message is None:
        print("Must have message")
        exit()

    else:
        instr = {"Action" : action,
                 "MsgID" : team + "$" + str(time.time()),
                 "Subject" : subject,
                 "Message" : args.message}

# If action is pull, either subject or message alone is allowed
elif action == 'pull':
    if message is None and subject is not None:
        instr = {"Action" : action,
                 "Subject" : subject}

    elif subject is None and message is not None:
        instr = {"Action" : action,
                 "Message" : message}

    else:
        instr = {"Action" : action,
                 "Subject" : subject,
                 "Message" : message}

else:
    print("Incorrect usage of the action argument. Push or pull only")
    exit()

# Inserting the data into the local repository
if action == 'push':
    post_id = posts.insert_one(instr).inserted_id

# Deleting the non-serializable object from the dictionary
instr.pop('_id', None)

# Serializing the data to send over Bluetooth sockets
msg = pickle.dumps(instr)

# Connecting to the Bluetooth bridge
sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
sock.connect((bd_addr, port))

# Sending the message
sock.send(msg)

data = sock.recv(size)

print(str(pickle.loads(data)))

sock.close()
