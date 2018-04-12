import sqlite3, os
from sqlite3 import Error

# page table
page_table = "CREATE TABLE IF NOT EXISTS pages (" \
             "id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT," \
             "title TEXT NOT NULL," \
             "body TEXT NOT NULL);"

# tag table with page table foreign key as added tags correspond to a page in the page table
tag_table = "CREATE TABLE IF NOT EXISTS tags (" \
            "id INTEGER PRIMARY KEY AUTOINCREMENT," \
            "name TEXT NOT NULL);"

# junction table to store tags on a page and entry of pairs already in table are ignored
page_tag_table = "CREATE TABLE IF NOT EXISTS page_tag (" \
                 "page_id INTEGER NOT NULL," \
                 "tag_id INTEGER NOT NULL," \
                 "PRIMARY KEY(page_id, tag_id) ON CONFLICT IGNORE," \
                 "FOREIGN KEY(page_id) REFERENCES pages(id)," \
                 "FOREIGN KEY(tag_id) REFERENCES tags(id));"


class Database(object):
    def __init__(self):
        self.path = os.path.dirname(os.path.realpath(__file__)) + u"\\wikiDB.db"
        self.conn = self.create_connection()

    def create_connection(self):
        """" create connection object to SQLite Database
         :return Connectin object or None"""
        try:
            conn = sqlite3.connect(self.path)
            return conn
        except Error as e:
            print(e)

        return None

    def close_connection(self):
        ''' Close the connection to the database'''
        self.conn.close()

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
            print("Table " + table_name + " deletion successful")
        except Error as e:
            print("Table deletion failed due to " + str(e))

    def insert_page(self, title, body):
        """ Insert a new page in the page table
            :param title: title for the new page
            :param body: content on the page
            :return: row id of new page"""
        c = self.conn.cursor()
        c.execute("INSERT INTO pages VALUES (null,?,?);",(title,body))
        self.conn.commit()
        return c.lastrowid

    def insert_tag(self, name):
        """ Insert a new page in the page table
            :param name: name of tag being created
            :return: row id of new tag"""
        c = self.conn.cursor()
        c.execute("INSERT INTO tags VALUES (null,?);",(name))
        self.conn.commit()
        return c.lastrowid

    def populate_junction_table(self):
        '''Automatically popular page_tag from entries in page and tag tables, table ignores duplicates'''
        c = self.conn.cursor()
        c.execute("INSERT INTO page_tag (page_id, tag_id) SELECT pages.id AS page_id,"
                  "tags.id AS tag_id FROM pages CROSS JOIN tags;")
        self.conn.commit()

    def insert_page_tag(self, p_id, t_id):
        """ Insert a new page in the page table
            :param p_id: id of the page in the page table the tag belongs to
            :param t_id: id of the tag in tag table
            :return: """
        c = self.conn.cursor()
        c.execute("INSERT INTO page_tag VALUES (?,?);",(p_id,t_id))
        self.conn.commit()

    def find_rows(self,select_columns,table_name,search_criteria=None,order_by=None,row_limit=0,offset=0,group_by=None,
                 having_criteria=None):
        '''
        Perform selection statement on single table
        :param select_columns: list of columns returned by selection statement
        :param table_name: table to be queried
        :param search_criteria: expressions to specify desired qualities of the rows in the table
        :param order_by: expression to order selection of rows from table
        :param row_limit: limit the number of rows searched from the table
        :param offset: specify first row selected from given conditions
        :param group_by: group rows together to be able to perform aggregate functions on them
        :param having_criteria: criteria for grouping selected rows
        :return:
        '''
        c = self.conn.cursor()
        c.execute("SELECT ? FROM ? ;", (select_columns,table_name))
        self.conn.commit()


    def update_table(self,table_name,items,search_criteria=None, order_by=None,row_limit=0, offset=0):
        ''' Update an entry in the pages table
        :param table_name: name of the table to be updated
        :param items: dictionary of column to change as key and new value as key value
        :param search_criteria: dictionary with columns to search for and value to look for
        :param order_by: dict of column names or column number with asc or desc values to order rows to be changed, ascending by default
        :param row_limit: limit number of rows to be changed
        :param offset: number of rows left unchanged from selection before altering table
        :return row ids of changed rows in table'''


    def delete_row(self,table_name, search_criteria):
        ''' Delete row from page table
        :param table_name: name of the table
        :param search_criteria: conditional expressions used for querying table
        :return '''



def main():

    new_db = Database()
    if new_db.conn is not None:
        # table operations
        new_db.create_table(page_table)
        new_db.create_table(tag_table)
        new_db.create_table(page_tag_table)
        # new_db.insert_page("Test Page 1", "I hope this works")
    else:
        print("Error creating database connection.")


if __name__ == '__main__':
    main()