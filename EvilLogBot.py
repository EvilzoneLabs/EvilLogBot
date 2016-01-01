'''
    Author: Kulverstukas
    Date: 2015.12.31
    Website: 9v.lt; Evilzone.org
    Description:
        EvilLogBot logs channel messages in raw format to an SQLite database and pulls out a
        specified amount of days worth of logs to be used. This bot is primarily developed to
        be used with PISG with a logrotate functionality.
'''

import socket
import string
import time

configs = {
    "server": "irc.evilzone.org",
    "channel": "#test",
    "port": 6667,
    "name": "StatBot"
}

def containsStatusId(data):
    return ((data == "451") or
        (data == "001") or
        (data == "002") or
        (data == "003") or
        (data == "004") or
        (data == "005") or
        (data == "251") or
        (data == "252") or
        (data == "254") or
        (data == "255") or
        (data == "265") or
        (data == "266") or
        (data == "375") or
        (data == "372") or
        (data == "376") or
        (data == "332") or
        (data == "333") or
        (data == "353") or
        (data == "422") or
        (data == "366"))

def begin():
    joined = False
    irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    irc.connect((configs["server"], configs["port"]))
    irc.send("NICK %s\r\n" % configs["name"])
    irc.send("USER {0} {0} {0} :Evil{0}\r\n".format(configs["name"]))
    while True:
        data = ""
        data = irc.recv(512)
        if (data.strip() != ""):
            dataParts = data.split()
            if "PING" in dataParts[0]: irc.send("PONG %s\r\n" % data.split(" :")[1])
            elif (not containsStatusId(dataParts[1]) and (dataParts[0][0] == ":")):
                print data
        
        if (not joined):
            irc.send("JOIN %s\r\n" % configs["channel"])
            joined = True
            
        if ((dataParts[1] == "KICK") and (dataParts[3] == configs["name"])):
            irc.send("JOIN %s\r\n" % configs["channel"])
            
begin()