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

#==============================================
class DB_module():

    configs = {
        "db_name": "EvilLogBot_logs.db",
        "table_name": "evilzone"
    }
    
    dbConn = None
    
    ''' Prepares the database for usage and returns a connection object '''
    def prepareDb(self):
        if (self.dbConn == None):
            self.dbConn = sqlite3.connect(self.configs["db_name"])
            self.dbConn.text_factory = str
            dbCurs = self.dbConn.cursor()
            # we should check if the defined table exists
            dbCurs.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (self.configs["table_name"],))
            rtn = dbCurs.fetchone()
            if (rtn == None):
                dbCurs.execute("CREATE TABLE {0} (time text, log text)".format(self.configs["table_name"]))
                self.dbConn.commit()
            dbCurs.close()
        return self.dbConn
    
    ''' Inserts given text into the database '''
    def insertLog(self, text):
        self.dbConn.cursor().execute("INSERT INTO {0} VALUES (?, ?)".format(self.configs["table_name"]), (str(int(time.time())), text))
        self.dbConn.commit()
    
    '''
        Function that removes rows that are older than
        defined number of days - 1 (justin case).
        This is some serious logrotate shit bruh.
    '''
    def cleanDb(self, logAge):
        rmPeriod = int(time.time() - timedelta(days=(int(logAge)+1)).total_seconds())
        self.dbConn.cursor().execute("DELETE FROM {0} WHERE time <= {1}".format(self.configs["table_name"], rmPeriod))
        self.dbConn.commit()

    def getLogs(self, logAge):
        logPeriod = int(time.time() - timedelta(days=logAge).total_seconds())
        return self.dbConn.cursor().execute("SELECT * FROM {0} WHERE time > {1}".format(self.configs["table_name"], str(logPeriod))).fetchall()
#==============================================
if __name__ == "__main__":
    exit("%s: Direct script execution is now allowed" % argv[0])