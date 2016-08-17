'''
    Author: Kulverstukas
    Date: 2016.08.15
    Website: 9v.lt; Evilzone.org
    Description:
        This is a database module for MySQL.
        P.S. MySQL docs for Python Connector sucks massive dick!!!
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
        "log_table_name": "logs"
    }
    
    dbConn = None
    
    ''' Prepares the database for usage and returns a connection object '''
    def prepareDb(self):
        self.dbConn = mysql.connector.connect(host=self.configs["db_host"],
                                     user=self.configs["db_user"],
                                     password=self.configs["db_passwd"],
                                     database=self.configs["db_name"],
                                     buffered=True)
        self.dbConn.cursor().execute("CREATE TABLE IF NOT EXISTS {0} (time text, log text)".format(self.configs["log_table_name"]))
        self.dbConn.cursor().execute("CREATE TABLE IF NOT EXISTS `ignore` (criteria text)")
        return self.dbConn
    
    ''' Inserts given text into the database '''
    def insertLog(self, text):
        curs = self.dbConn.cursor()
        curs.execute("INSERT INTO {0} VALUES ('{1}', '{2}')".format(self.configs["log_table_name"], str(int(time.time())), text))
        self.dbConn.commit()
        curs.close()
    
    '''
        Function that removes rows that are older than
        defined number of days - 1 (justin case).
        This is some serious logrotate shit bruh.
    '''
    def cleanDb(self, logAge):
        rmPeriod = int(time.time() - timedelta(days=(int(logAge)+1)).total_seconds())
        curs = self.dbConn.cursor()
        curs.execute("DELETE FROM {0} WHERE time <= {1}".format(self.configs["log_table_name"], rmPeriod))
        self.dbConn.commit()
        curs.close()

    def getLogs(self, logAge):
        logPeriod = int(time.time() - timedelta(days=logAge).total_seconds())
        curs = self.dbConn.cursor()
        curs.execute("SELECT * FROM {0} WHERE time > {1}".format(self.configs["log_table_name"], str(logPeriod)))
        res = curs.fetchall()
        curs.close()
        return res
        
    def shouldIgnore(self, criteria):
        curs = self.dbConn.cursor()
        curs.execute("SELECT * FROM `ignore` WHERE LOWER(criteria) = '{0}'".format(criteria.lower()))
        res = curs.fetchall()
        curs.close()
        return (len(res) > 0)
        
    def addToIgnore(self, nickname):
        curs = self.dbConn.cursor()
        curs.execute("INSERT INTO `ignore` VALUES ('{0}')".format(nickname))
        self.dbConn.commit()
        curs.close()
        
    def delFromIgnore(self, nickname):
        curs = self.dbConn.cursor()
        curs.execute("DELETE FROM `ignore` WHERE criteria = '{0}'".format(nickname))
        self.dbConn.commit()
        curs.close()
#==============================================
if __name__ == "__main__":
    exit("%s: Direct script execution is not allowed" % argv[0])