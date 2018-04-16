from io import open
import os
import shutil
from sqlite3 import Error
from tempfile import mkdtemp
from unittest import TestCase

from wiki.core import Wiki
from wiki.web import create_app
from wiki.Database import Database

#: the default configuration
CONFIGURATION = u"""
PRIVATE=False
TITLE='test'
DEFAULT_SEARCH_IGNORE_CASE=False
DEFAULT_AUTHENTICATION_METHOD='hash'
"""

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


class WikiBaseTestCase(TestCase):

    #: The contents of the ``config.py`` file.
    config_content = CONFIGURATION

    def setUp(self):
        """
            Creates a content directory for the wiki to use
            and adds a configuration file with some example content.
        """
        self._wiki = None
        self._app = None
        self.rootdir = mkdtemp()
        self.create_file(u'config.py', self.config_content)

    @property
    def wiki(self):
        if not self._wiki:
            self._wiki = Wiki(self.rootdir)
        return self._wiki

    @property
    def app(self):
        if not self._app:
            self._app = create_app(self.rootdir).test_client()
        return self._app

    def create_file(self, name, content=u'', folder=None):
        """
            Easy way to create a file.

            :param unicode name: the name of the file to create
            :param unicode content: content of the file (optional)
            :param unicode folder: the folder where the file should be
                created, defaults to the temporary directory

            :returns: the absolute path of the newly created file
            :rtype: unicode
        """
        if folder is None:
            folder = self.rootdir

        path = os.path.join(folder, name)

        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        with open(path, 'w', encoding='utf-8') as fhd:
            fhd.write(content)

        return path


    def tearDown(self):
        """
            Will remove the root directory and all contents if one
            exists.
        """
        if self.rootdir and os.path.exists(self.rootdir):
            shutil.rmtree(self.rootdir)

    @staticmethod
    def create_test_database():
        """
        Create a test database modeled after wiki database to perform operation on for testing
        """
        # create new Database object that connects to test database
        testDB = Database("testDB")
        try:
            testDB.create_table(page_table)
            testDB.create_table(tag_table)
            testDB.create_table(page_tag_table)
        except Error as e:
            print(e)
