import sqlite3, os
from sqlite3 import Error

# page table
page_table = "CREATE TABLE IF NOT EXISTS pages (" \
             "id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT," \
             "name TEXT NOT NULL," \
             "title TEXT NOT NULL," \
             "body TEXT NOT NULL);"

# tag table with page table foreign key as added tags correspond to a page in the page table
tag_table = "CREATE TABLE IF NOT EXISTS tags (" \
            "name TEXT PRIMARY KEY NOT NULL);"

# junction table to store tags on a page and entry of pairs already in table are ignored
page_tag_table = "CREATE TABLE IF NOT EXISTS page_tag (" \
                 "page_id INTEGER NOT NULL," \
                 "tag_id TEXT NOT NULL," \
                 "PRIMARY KEY(page_id, tag_id) ON CONFLICT IGNORE," \
                 "FOREIGN KEY(page_id) REFERENCES pages(id)," \
                 "FOREIGN KEY(tag_id) REFERENCES tags(name));"


class Database(object):
    def __init__(self, database_name):
        self.path = os.path.dirname(os.path.realpath(__file__)) + "\\%s.db" % database_name
        self.conn = self.create_connection()

    def create_connection(self):
        """" create connection object to SQLite Database and create database if it doesn't exist
         :return Connectin object or None"""
        try:
            conn = sqlite3.connect(self.path)
            return conn
        except Error as e:
            print(e)

        return None

    def close_connection(self):
        ''' Close the connection to the database'''
        try:
            self.conn.close()
        except Error as e:
            print(e)

    def create_table(self, create_string):
        """ create a table in database using sql string
        :param create_string: the sql statement to create table
        :return:
        """
        try:
            c = self.conn.cursor()
            c.execute(create_string)
            self.conn.commit()
        except Error as e:
            print(e)

    def drop_table(self, table_name):
        """ Drop a table within the database
            :param table_name: name of table to be deleted
            :return: message indicating table deletion successful or failed
            """
        try:
            c = self.conn.cursor()
            c.execute("DROP TABLE " + table_name)
            self.conn.commit()
        except Error as e:
            print(e)

    def insert_page(self, name, title, body):
        """ Insert a new page in the page table
            :param name: name of the page
            :param title: title for the new page
            :param body: content on the page
            :return: """
        try:
            c = self.conn.cursor()
            c.execute("INSERT INTO pages VALUES (null,?,?,?)",(name, title, body))
            self.conn.commit()
        except Error as e:
            print(e)

    def insert_tag(self, name):
        """ Insert a new page in the page table
            :param name: name of tag being created
            :return: """
        try:
            c = self.conn.cursor()
            c.execute("INSERT INTO tags VALUES (?)",(name,))
            self.conn.commit()
        except Error as e:
            print(e)

    def insert_page_tag(self,page_num,tag_name):
        '''Insert an entry into the junction table for each tag on a page'''
        try:
            c = self.conn.cursor()
            c.execute("INSERT INTO page_tag (page_id, tag_id) VALUES (?,?)", (page_num,tag_name))
            self.conn.commit()
        except Error as e:
            print(e)

    def find_rows(self, select_columns, table_name, count=False, search_criteria=None, order_by=None, row_limit=0, offset=0,
                  group_by=None, having_criteria=None):
        """
        Perform selection statement on single table, input must be given in sql style
        :param select_columns: string of columns returned by selection statement separated by commas
        :param table_name: table to be queried
        :param count: determine whether to use the COUNT function or not. (CAN LATER BE CHANGED TO ACCOUNT
        FOR OTHER SPECIAL CASES WITH SELECT STATEMENTS)
        :param search_criteria: expressions to specify desired qualities of the rows in the table
        :param order_by: expression to order selection of rows from table
        :param row_limit: limit the number of rows searched from the table
        :param offset: specify first row selected from given conditions
        :param group_by: group rows together to be able to perform aggregate functions on them
        :param having_criteria: criteria for grouping selected rows
        :return: list of rows from query
        """
        try:
            c = self.conn.cursor()
            if count is False:
                query = "SELECT %s FROM %s" % (select_columns, table_name)
            else:
                query = "SELECT COUNT(%s) FROM %s" % (select_columns, table_name)
            if search_criteria is not None:
                query = query + (" WHERE %s" % search_criteria)
            if order_by is not None:
                query = query + (" ORDER BY %s" % order_by)
            if row_limit is not 0:
                query = query + (" LIMIT %s" % str(row_limit))
            if offset is not 0:
                query = query + (" OFFSET %s" % str(offset))
            if group_by is not None:
                query = query + (" GROUP BY %s" % group_by)
            if having_criteria is not None:
                query = query + (" HAVING %s" % having_criteria)
            # c.execute(query)
            # self.conn.commit()
            # return c.fetchall()
            return query
        except Error as e:
            print(e)


    def update_table(self, table_name, change_cols, change_values, search_criteria=None, order_by=None,
                     row_limit=0, offset=0):
        """ Update an entry in the pages table
        :param table_name: name of the table to be updated
        :param change_cols: a list of the columns to be changed in update statement
        :param change_values: a list of the values in each column to be changed.
        :param search_criteria: filter for query
        :param order_by: column to sort query and in what direction DESC by default
        :param row_limit: limit number of rows to be changed
        :param offset: number of rows left unchanged from selection before altering table
        :return row ids of changed rows in table"""

        try:
            c = self.conn.cursor()
            # establish initial line with first required change to table with for loop for multiple changes
            query = "UPDATE %s SET %s = '%s'" % (table_name, change_cols[0], change_values[0])
            if len(change_cols) > 1:
                for i in range(1, len(change_cols)):
                    query = query + ", %s = '%s'" % (change_cols[i], change_values[i])
            if search_criteria is not None:
                query = query + " WHERE %s" % search_criteria
            if order_by is not None:
                query = query + (" ORDER BY %s" % order_by)
            if row_limit is not 0:
                query = query + (" LIMIT %s" % str(row_limit))
            if offset is not 0:
                query = query + (" OFFSET %s" % str(offset))
            # c.execute(query)
            # self.conn.commit()
            return query
        except Error as e:
            print(e)


    def delete_row(self,table_name, search_criteria = None):
        ''' Delete row from page table
        :param table_name: name of the table
        :param search_criteria: conditional expressions used for querying table
        :return id of row deleted'''

        try:
            c = self.conn.cursor()
            # establish initial line with first required change to table with for loop for multiple changes
            query = "DELETE FROM %s" % table_name
            if search_criteria is not None:
                query = query + " WHERE %s" % search_criteria
            c.execute(query)
            self.conn.commit()
        except Error as e:
            print(e)


def main():
    new_db = Database("wikiDB")
    if new_db.conn is not None:
        # table operations
        new_db.create_table(page_table)
        new_db.create_table(tag_table)
        new_db.create_table(page_tag_table)
    else:
        print("Error creating database connection.")


if __name__ == '__main__':
    main()