from core import Page
from wiki.Database import Database

from tests import WikiBaseTestCase

PAGE_CONTENT_1 = u"""\
title: Test1
tags: one, two, 3

Hello, how are you guys?

**Is it not _magnificent_**?
"""

PAGE_CONTENT_2 = u"""\
title: Test2
tags: a, b, c, d

Test test test
"""

PAGE_CONTENT_3 = u"""\
title: Not_Test
tags: z, one, d

Woo!
"""

PAGE_CONTENT_4 = u"""\
title: title
tags: fdfd

Stuff!
"""

PAGE_NAME_1 = "page1.md"
PAGE_NAME_2 = "page2.md"
PAGE_NAME_3 = "page3.md"
PAGE_NAME_4 = "page4.md"
URL_1 = "page1"
URL_2 = "page2"
URL_3 = "page3"
URL_4 = "page4"


WIKILINK_CONTENT_HTML = u"""\
<p><a href='/target'>target</a></p>"""


class DatabaseTestCase(WikiBaseTestCase):
    """
        Contains database operation tests for the :class:`~wiki.Database.Database`
        class.
    """
    page_1 = None
    page_2 = None
    page_3 = None
    page_4 = None
    all_pages = []

    # create test database using function in __init__.py
    WikiBaseTestCase.create_test_database()
    testDB = Database("testDB")

    # create cursor object to execute sql statements on database
    c = testDB.conn.cursor()

    def setUp(self):
        # setup wiki content directory and config file
        super(DatabaseTestCase, self).setUp()

        # create files to be inserted into the database
        page_path_1 = self.create_file(PAGE_NAME_1, PAGE_CONTENT_1)
        page_path_2 = self.create_file(PAGE_NAME_2, PAGE_CONTENT_2)
        page_path_3 = self.create_file(PAGE_NAME_3, PAGE_CONTENT_3)
        page_path_4 = self.create_file(PAGE_NAME_4, PAGE_CONTENT_4)

        # have the class variables reference the new pages
        self.page_1 = Page(page_path_1, URL_1)
        self.page_2 = Page(page_path_2, URL_2)
        self.page_3 = Page(page_path_3, URL_3)
        self.page_4 = Page(page_path_4, URL_4)
        self.all_pages.append(self.page_1)
        self.all_pages.append(self.page_2)
        self.all_pages.append(self.page_3)
        self.all_pages.append(self.page_4)

    def test_database_operations(self):
        """
        Test database connection function and high-level operations on tables like table creation and deletion
        """
        # Test database creation
        self.assertIsNot(self.testDB.conn,None)

        # Test table manipulation
        self.testDB.create_table("CREATE TABLE IF NOT EXISTS test_table ("
                                 "id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, "
                                 "title TEXT NOT NULL, body TEXT NOT NULL);")
        self.c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_table';")
        new_table = self.c.fetchone()[0]
        self.assertEquals(new_table,"test_table")

        self.testDB.drop_table("test_table")
        self.c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_table';")
        new_table = self.c.fetchone()
        self.assertEquals(new_table, None)

    def get_table_size(self, table_name):
        self.c.execute("SELECT COUNT (*) FROM %s" % table_name)
        table_size = self.c.fetchone()[0]
        return table_size

    def test_table_insert_operations(self):
        """
        Test insertion of elements into page and tags table then test function to populate junction table
        """

        # reset the tables for new test entries
        init_page_rows = self.get_table_size("pages")
        init_tags_rows = self.get_table_size("tags")
        init_page_tag_rows = self.get_table_size("page_tag")
        if init_page_rows > 0:
            self.testDB.delete_row("pages")
            self.testDB.delete_row("sqlite_sequence", "name = 'pages'")
        if init_tags_rows > 0:
            self.testDB.delete_row("tags")
            self.testDB.delete_row("sqlite_sequence", "name = 'tags'")
        if init_page_tag_rows > 0:
            self.testDB.delete_row("page_tag")

    # test the insert function for the page table
        self.testDB.insert_page(self.page_1.url, self.page_1.title, self.page_1.body)
        self.testDB.insert_page(self.page_2.url, self.page_2.title, self.page_2.body)
        self.testDB.insert_page(self.page_3.url, self.page_3.title, self.page_3.body)
        self.testDB.insert_page(self.page_4.url, self.page_4.title, self.page_4.body)
        self.c.execute("SELECT COUNT (*) FROM pages")
        num_rows = self.c.fetchone()[0]
        self.assertEquals(num_rows, 4)

        # test the insert function for the tags table
        for page in self.all_pages:
            tags_list = [x.strip() for x in page.tags.split(',')]
            for tag in tags_list:
                self.testDB.insert_tag(tag)
        self.c.execute("SELECT COUNT (*) FROM tags")
        num_rows = self.c.fetchone()[0]
        self.assertEquals(num_rows, 9)

        # test the insert function for the page_tag junction table, inserts one entry for each tag on a page
        for page in self.all_pages:
            self.c.execute("SELECT id FROM pages WHERE name = ? AND title = ?;", (page.url, page.title))
            page_id = self.c.fetchone()[0]
            tags_list = [x.strip() for x in page.tags.split(',')]
            for tag in tags_list:
                self.testDB.insert_page_tag(page_id, tag)
        self.c.execute("SELECT COUNT (*) FROM page_tag")
        num_rows = self.c.fetchone()[0]
        self.assertEquals(num_rows, 11)

    def test_table_read_operations(self):
        """
        Test search operations on the table
        """

        selected_list = self.testDB.find_rows("*", "pages", False, "title LIKE '%test%'")  # page 1,2,3

        # testing query string creation process
        # self.assertEquals(test_query, "SELECT COUNT(*) FROM pages WHERE title LIKE '%test%'")

        # testing select functionality
        for row in selected_list:
            print(row)
        self.assertEquals(len(selected_list), 3)

    def test_table_manipulation_operations(self):
        """
        Test update and delete operations on the table
        """

        # test_query = self.testDB.update_table("pages", ["name"], ["updated_name"], "body LIKE '%are%'")  # page 1
        self.testDB.update_table("pages", ["name"], ["updated_name"], "body LIKE '%are%'")  # page 1

        # testing query creation process
        # self.assertEquals(test_query, "UPDATE pages SET name = 'updated_name' WHERE body LIKE '%are%'")

        # testing update functionality
        self.c.execute("SELECT COUNT (*) FROM pages WHERE name = 'updated_name'")
        pages_updated = self.c.fetchone()[0]
        self.assertEquals(pages_updated, 1)