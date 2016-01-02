'''
    Author: Kulverstukas
    Date: 2015.12.31
    Website: 9v.lt; Evilzone.org
    Description:
        EvilLogBot logs channel messages in raw format with a UNIX timestamp to an SQLite database and pulls out a specified amount of days worth of logs to be used with a log file analyzer like PISG. The time format of a generated log is set to zbot's, because it's easiest to manage without parsing anything (except the time, ofcourse).
        This bot is primarily developed to be used with PISG on an EvilZone network and have an inbuilt logrotate functionality, but I tried to make it as generic as I can to work on other networks as well.
'''

import socket
import string
import time
import sqlite3
import re
import cgi
from sys import argv
from datetime import timedelta

#==============================================
configs = {
    "server": "vader.irc.evilzone.org",
    "channel": "#test",
    "port": 6667,
    "name": "StatBot",
    "db_name": "EvilLogBot_logs.db",
    "log_name": "evilzone_logs.txt",
    "table_name": "evilzone",
    # let's us zbot's format, easiest format to deal with :)
    "time_format": "%m/%d/%y %H:%M:%S",
    "log_age": 60 # in days
}
#==============================================
def containsStatusId(data):
    """ Checks if a received line of data contains a status code which we should skip (motd etc...) """
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
#==============================================
def prepDb():
    """ Preps the database for usage """
    dbConn = sqlite3.connect(configs["db_name"])
    dbConn.text_factory = str
    dbCurs = dbConn.cursor()
    # we should check if the defined table exists
    dbCurs.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (configs["table_name"],))
    rtn = dbCurs.fetchone()
    if (rtn == None):
        dbCurs.execute("CREATE TABLE {0} (time text, log text)".format(configs["table_name"]))
        dbConn.commit()
    return dbConn
#==============================================
def exportLog():
    """ Method to export a given length of days.
        Strips HTML (not entities) for security. """
    dbConn = prepDb()
    dbCurs = dbConn.cursor()
    logPeriod = int(time.time() - timedelta(days=configs["log_age"]).total_seconds())
    dbCurs.execute("SELECT * FROM {0} WHERE time > {1}".format(configs["table_name"], str(logPeriod)))
    rtn = dbCurs.fetchall()
    tag_re = re.compile(r'(<!--.*?-->|<[^>]*>)')
    with open(configs["log_name"], "w") as f:
        for row in rtn:
            t = time.strftime(configs["time_format"], time.gmtime(float(row[0])))
            stripped = cgi.escape(tag_re.sub("", row[1]))
            f.write("%s %s" % (t, stripped))
#==============================================
def connect():
    joined = False
    dbConn = prepDb()
    dbCurs = dbConn.cursor()
    irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    irc.connect((configs["server"], configs["port"]))
    irc.send("NICK %s\r\n" % configs["name"])
    irc.send("USER {0} {0} {0} :Evil{0}\r\n".format(configs["name"]))
    while True:
        data = ""
        data = irc.recv(512)
        if (data.strip() != ""):
            dataParts = data.split()
            if ("PING" in dataParts[0]): irc.send("PONG %s\r\n" % data.split(" :")[1])
            elif (not containsStatusId(dataParts[1]) and (dataParts[0][0] == ":") and (dataParts[2] != configs["name"])):
                dbCurs.execute("INSERT INTO {0} VALUES ('{1}', '{2}')".format(configs["table_name"], str(time.time()), data.strip()))
                dbConn.commit()
                # print data
        
        if (not joined):
            irc.send("JOIN %s\r\n" % configs["channel"])
            joined = True
            
        if ((dataParts[1] == "KICK") and (dataParts[3] == configs["name"])):
            irc.send("JOIN %s\r\n" % configs["channel"])
#==============================================

if __name__ == "__main__":
    if (len(argv) > 1):
        if (argv[1] == "export"):
            exportLog()
        else:
            print "Usage: %s [export]" % argv[0]
    else:
        pass
        # begin()