'''
    Author: Kulverstukas
    Date: 2016.08.15
    Website: 9v.lt; Evilzone.org
    Description:
        This is a database module for MySQL.
'''

from sys import argv
from datetime import timedelta
import time
import mysql.connector

#==============================================
class DB_module():

    configs = {
        "db_host": "127.0.0.1",
        "db_user": "root",
        "db_passwd": "",
        "db_name": "evilzone_logs",
        "table_name": "logs"
    }
    
    dbConn = None
    
    ''' Prepares the database for usage and returns a connection object '''
    def prepareDb(self):
        try:
            self.dbConn = mysql.connector.connect(host=self.configs["db_host"],
                                         user=self.configs["db_user"],
                                         password=self.configs["db_passwd"],
                                         database=self.configs["db_name"])
            self.dbConn.cursor().execute("CREATE TABLE {0} (time text, log text)".format(self.configs["table_name"]))
        except mysql.connector.Error as err:
            if err.errno != 1050: # errorcode.ER_TABLE_EXISTS_ERROR
                exit(err.msg)
        return self.dbConn
    
    ''' Inserts given text into the database '''
    def insertLog(self, text):
        self.dbConn.cursor().execute("INSERT INTO {0} VALUES (%s, %s)".format(self.configs["table_name"]), (str(int(time.time())), text))
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