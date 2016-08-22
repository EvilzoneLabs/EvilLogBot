'''
    Author: Kulverstukas
    Date: 2015.12.31
    Last update: 2016.08.13
    Website: 9v.lt; Evilzone.org
    Description:
        EvilLogBot logs channel messages in raw format with a UNIX timestamp to an SQLite database and pulls out a specified amount of days worth of logs to be used with a log file analyzer like PISG. The time format of a generated log is set to zbot's, because it's easiest to manage without parsing anything (except the time, ofcourse).
        This bot is primarily developed to be used with PISG on an EvilZone network and have an inbuilt logrotate functionality, so it may not work with other networks.
'''

import socket
import string
import time
import re
import cgi
import traceback
import sys
from sys import argv

#==============================================
# change this import statement to whatever module you would like to use

# from sqlite_module import DB_module
from mysql_module import DB_module

dbManager = DB_module()
dbManager.prepareDb()
#==============================================
configs = {
    "server": "irc.evilzone.org",
    "channel": "#test",
    "port": 6667,
    "name": "NewStatsBot",
    "log_name": "evilzone_logs.txt",
    # let's use zbot's format, easiest format to deal with :)
    "time_format": "%m/%d/%y %H:%M:%S",
    "log_age": 1 # in days
}
#==============================================
def shouldLogThis(data):
    """ Checks if a received line of data contains what we should save. """
    match = re.search(r":.+?!.+?@.+?$", data)
    return (match is not None) # if it contains a user
#==============================================
def exportLog():
    """ Method to export a given length of days.
        Strips HTML (not entities) for security. """
    dbManager.cleanDb(configs["log_age"])
    logs = dbManager.getLogs(configs["log_age"])
    tag_re = re.compile(r'(<!--.*?-->|<[^>]*>)')
    with open(configs["log_name"], "w") as f:
        for row in logs:
            rowLines = row[1].split("\r\n")
            for line in rowLines:
                try:
                    t = time.strftime(configs["time_format"], time.gmtime(float(row[0])))
                    stripped = cgi.escape(tag_re.sub("", line))
                    f.write("%s %s\n" % (t, stripped))
                except:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
                    with open("parse_errors.txt", "a") as g:
                        g.write(''.join(line for line in lines))
                        g.write("\r\n")
                    continue
#==============================================
def connect():
    firstPing = False
    irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    irc.connect((configs["server"], configs["port"]))
    irc.send("NICK %s\r\n" % configs["name"])
    irc.send("USER {0} {0} {0} :Evil{0}\r\n".format(configs["name"]))
    while True:
        rawData = ""
        rawData = irc.recv(4096)
        if (rawData.strip() != ""):
            try:
                dataLines = rawData.split("\r\n")
                for data in dataLines:
                    dataParts = data.split()
                    if (len(dataParts) > 2):
                        # print dataParts
                        if ((dataParts[1] == "KICK") and (dataParts[3] == configs["name"])):
                            irc.send("JOIN %s\r\n" % configs["channel"])
                            continue
                        elif ((dataParts[0] == "ERROR") and (dataParts[1] == ":Closing")):
                            irc.close()
                            return False
                    if ((len(dataParts) > 1) and (shouldLogThis(dataParts[0]))):
                        match = re.search(r":.+?!", dataParts[0])
                        if match:
                            nickname = match.group(0)[1:-1]
                            if (dbManager.shouldIgnore(nickname)):
                                continue
                        dbManager.insertLog(data.strip())
                        print data
                    elif ((len(dataParts) > 0) and ("PING" in dataParts[0])):
                            irc.send("PONG %s\r\n" % data.split(" :")[1])
                            # print "sent"
                            if (not firstPing):
                                irc.send("JOIN %s\r\n" % configs["channel"])
                                firstPing = True
            except:
                with open("connection_errors.txt", "a") as g:
                        g.write(traceback.format_exc())
                        g.write("\r\n")
                continue
#==============================================

if __name__ == "__main__":
    if (len(argv) > 1):
        if (argv[1] == "export"):
            exportLog()
        elif ((argv[1] == "ignore") and (len(argv) > 3)):
            if (argv[2] == "add"):
                dbManager.addToIgnore(argv[3])
                print "%s added to ignore list" % argv[3]
            elif (argv[2] == "del"):
                dbManager.delFromIgnore(argv[3])
                print "%s deleted from ignore list" % argv[3]
        elif ((argv[1] == "ignore") and (len(argv) > 2) and (argv[2] == "list")):
            for counter, person in enumerate(dbManager.listIgnored()):
                print "[%d] %s" % (counter, person[0])
        else:
            print "Usage: %s [export]" % argv[0]
            print "       %s ignore [add/del/list] <nickname>" % argv[0]
    else:
        # pass
        while True:
            # connection was killed somehow
            connect()