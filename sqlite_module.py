'''
    Author: Kulverstukas
    Date: 2016.08.15
    Website: 9v.lt; Evilzone.org
    Description:
        This is a database module for SQLite.
'''

from sys import argv
from datetime import timedelta
import time
import sqlite3
import string

#==============================================
class DB_module():

    configs = {
        "db_name": "EvilLogBot_logs.db",
        "log_table_name": "evilzone"
    }
    
    dbConn = None
    
    ''' Prepares the database for usage and returns a connection object '''
    def prepareDb(self):
        if (self.dbConn == None):
            self.dbConn = sqlite3.connect(self.configs["db_name"])
            self.dbConn.text_factory = str
            self.dbConn.cursor().execute("CREATE TABLE IF NOT EXISTS {0} (time text, log text)".format(self.configs["log_table_name"]))
            self.dbConn.cursor().execute("CREATE TABLE IF NOT EXISTS 'ignore' (criteria text)")
            self.dbConn.commit()
        return self.dbConn
    
    ''' Inserts given text into the database '''
    def insertLog(self, text):
        self.dbConn.cursor().execute("INSERT INTO {0} VALUES (?, ?)".format(self.configs["log_table_name"]), (str(int(time.time())), text))
        self.dbConn.commit()
    
    '''
        Function that removes rows that are older than
        defined number of days - 1 (justin case).
        This is some serious logrotate shit bruh.
    '''
    def cleanDb(self, logAge):
        rmPeriod = int(time.time() - timedelta(days=(int(logAge)+1)).total_seconds())
        self.dbConn.cursor().execute("DELETE FROM {0} WHERE time <= {1}".format(self.configs["log_table_name"], rmPeriod))
        self.dbConn.commit()

    def getLogs(self, logAge):
        logPeriod = int(time.time() - timedelta(days=logAge).total_seconds())
        return self.dbConn.cursor().execute("SELECT * FROM {0} WHERE time > {1}".format(self.configs["log_table_name"], str(logPeriod))).fetchall()
        
    def shouldIgnore(self, criteria):
        return (len(self.dbConn.cursor().execute("SELECT * FROM 'ignore' WHERE LOWER(criteria) = '{0}'".format(criteria.lower())).fetchall()) > 0)
        
    def addToIgnore(self, nickname):
        self.dbConn.cursor().execute("INSERT INTO `ignore` VALUES (?)", (nickname,))
        self.dbConn.commit()
        
    def delFromIgnore(self, nickname):
        self.dbConn.cursor().execute("DELETE FROM `ignore` WHERE criteria = '{0}'".format(nickname))
        self.dbConn.commit()
        
    def listIgnored(self):
        return self.dbConn.cursor().execute("SELECT * FROM `ignore`").fetchall()
#==============================================
if __name__ == "__main__":
    exit("%s: Direct script execution is not allowed" % argv[0])