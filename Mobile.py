#!usr/bin/env python3

import sys
import time
import argparse
import pymongo

from pymongo import MongoClient

team = "12"

client = MongoClient('localhost', 27017)
db = client['test_database'] # Using the database provided by MongoDB
posts = db.posts
count = posts.count() # Number of records in database

parser = argparse.ArgumentParser()

# The first 2 arguments are required but message argument isn't
# (Seemed to be that way from the assignment specs)

parser.add_argument("-a", "--action", type = str,
                    required = True,
                    help = "push or pull messages")
parser.add_argument("-s", "--subject", type = str,
                    required = True,
                    help = "subject of the message")
parser.add_argument("-m", "--message", type = str,
                    required = False,
                    help = "message to be pusshed or pulled")

args = parser.parse_args()

action = args.action
subject = args.subject

# Make it so the formats of each of the message instructions
# are different based on the action as well
# Pull action does not need MsgID for it unlike push

if args.message:
    instr = {"Action" : action,
             "MsgID" : team + "$" + str(time.time()),
             "Subject" : subject,
             "Message" : args.message}

else:
    instr = {"Action" : action,
             "MsgID" : team + "$" + str(time.time()),
             "Subject" : subject}


# These parts below will be in the repository pi
# They are just here to be tested before use and
# to make sure the MongoDB stuff itself is working

if action == 'push':
    post_id = posts.insert_one(instr).inserted_id

    if post.count() > count:
        output = {"Status" : "Success"}

    else:
        output = {"Status" : "Fail"}

    print(output)
    

elif action == 'pull':
    for post in posts.find({"Subject" : subject}):
        output = {"MsgID" : post['MsgID'],
                  "Message" : post['Message']}
        print(output)

# Next part for the client will be to print out
# the message that is received from the bridge pi
# after that receives its message from the repository
