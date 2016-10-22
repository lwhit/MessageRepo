#!/usr/bin/env python3
import bluetooth

#hostMACAddress = 'B8:27:EB:F0:A7:D7'

port = 3
backlog = 1
size = 1024
s = bluetooth.BluetoothSocket( bluetooth.RFCOMM )

s.bind(('', port))
s.listen(backlog)

try:
    client, clientInfo = s.accept()
    print("Server Started!\n\n")
    while 1:
        data = client.recv(size)
        if data:
            print(data)
            client.send(data)
except:
    print("Closing socket")
    client.close()
    s.close()