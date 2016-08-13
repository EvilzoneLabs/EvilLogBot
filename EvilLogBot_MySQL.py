'''
    Author: Kulverstukas
    Date: 2016.08.13
    Website: 9v.lt; Evilzone.org
    Description:
        EvilLogBot_MySQL logs channel messages in raw format with a UNIX timestamp to a MySQL database, skipping status and other non-relevant text as much as it can.
        This bot is primarily developed to be used with an EvilZone network and have an inbuilt logrotate functionality, so it may not work with other networks.
        Download the library from http://dev.mysql.com/downloads/file/?id=458967
'''

import socket
import string
import time
import mysql.connector
from mysql.connector import errorcode
import re
import cgi
import traceback
import sys
from sys import argv
from datetime import timedelta

#==============================================
configs = {
    "server": "irc.evilzone.org",
    "channel": "#test",
    "port": 6667,
    "name": "NewStatsBot",
    "log_name": "evilzone_logs.txt",
    "db_host": "127.0.0.1",
    "db_user": "root",
    "db_passwd": "",
    "db_name": "evilzone_logs",
    "log_table_name": "logs",
    # let's use zbot's format, easiest format to deal with :)
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
    try:
        dbConn = mysql.connector.connect(host=configs["db_host"],
                                     user=configs["db_user"],
                                     password=configs["db_passwd"],
                                     database=configs["db_name"])
        dbCurs = dbConn.cursor()
        dbCurs.execute("CREATE TABLE {0} (time text, log text)".format(configs["log_table_name"]))
    except mysql.connector.Error as err:
        if err.errno != errorcode.ER_TABLE_EXISTS_ERROR:
            exit(err.msg)
    dbCurs.close()
    return dbConn
#==============================================
def cleanDb(dbConn):
    """ Function that removes rows that are older than
        defined number of days - 1 (justin case).
        This is some serious logrotate shit bruh."""
    if (dbConn == None): dbConn = prepDb()
    dbCurs = dbConn.cursor()
    rmPeriod = int(time.time() - timedelta(days=(configs["log_age"]+1)).total_seconds())
    dbCurs.execute("DELETE FROM {0} WHERE time <= {1}".format(configs["log_table_name"], rmPeriod))
    dbConn.commit()
    dbCurs.close()
#==============================================
def exportLog():
    """ Method to export a given length of days.
        Strips HTML (not entities) for security. """
    dbConn = prepDb()
    cleanDb(dbConn)
    dbCurs = dbConn.cursor()
    logPeriod = int(time.time() - timedelta(days=configs["log_age"]).total_seconds())
    dbCurs.execute("SELECT * FROM {0} WHERE time > {1}".format(configs["log_table_name"], str(logPeriod)))
    rtn = dbCurs.fetchall()
    tag_re = re.compile(r'(<!--.*?-->|<[^>]*>)')
    with open(configs["log_name"], "w") as f:
        for row in rtn:
            # additional cleaning done here, should remove this once proper checking is done in connect()
            rowLines = row[1].split("\r\n")
            for line in rowLines:
                try:
                    status = line.split()
                    if (len(status) > 1):
                        if (containsStatusId(status[1]) or (status[1] == "NOTICE") or (status[0] == "PING")):
                            continue
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
    dbConn = prepDb()
    dbCurs = dbConn.cursor()
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
                        if ((dataParts[1] == "KICK") and (dataParts[3] == configs["name"])):
                            irc.send("JOIN %s\r\n" % configs["channel"])
                            continue
                        elif ((dataParts[0] == "ERROR") and (dataParts[1] == ":Closing")):
                            irc.close()
                            dbCurs.close()
                            dbConn.close()
                            return False
                    if ((len(dataParts) > 1) and (not containsStatusId(dataParts[1])) and (dataParts[0][0] == ":")):
                        dbCurs.execute("INSERT INTO {0} VALUES (%s, %s)".format(configs["log_table_name"]), (str(int(time.time())), data.strip()))
                        dbConn.commit()
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
        else:
            print "Usage: %s [export]" % argv[0]
    else:
        while True:
            # connection was killed somehow
            connect()