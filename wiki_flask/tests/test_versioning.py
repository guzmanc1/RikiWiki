from wiki.core import Page

from tests import WikiBaseTestCase

PAGE_CONTENT_1 = u"""\
title: Test
tags: one, two, 3

Hello, how are you guys?

**Is it not _magnificent_**?
"""

PAGE_CONTENT_2 = u"""\
title: Test
tags: a, b, c, d

Test test test

"""

PAGE_CONTENT_3 = u"""\
title: Not_Test
tags: z

Woo!

"""

PAGE_CONTENT_4 = u"""\
title: title
tags: fdfd

Stuff!

"""

PAGE_NAME_1 = "name_v1.md"

PAGE_NAME_2 = "test_v1.md"

PAGE_NAME_3 = "test_v2.md"

PAGE_NAME_4 = "file_v1.md"

URL_1 = "name_v1"

URL_2 = "test_v1"

URL_3 = "test_v2"

URL_4 = "file_v1"


WIKILINK_CONTENT_HTML = u"""\
<p><a href='/target'>target</a></p>"""

class PageTestCase(WikiBaseTestCase):
    """
        Contains versions tests for the :class:`~wiki.core.Page`
        class.
    """
    page_1 = None
    page_2 = None
    page_3 = None
    page_4 = None

    def setUp(self):
        super(PageTestCase, self).setUp()

        page_path_1 = self.create_file(PAGE_NAME_1, PAGE_CONTENT_1)
        page_path_2 = self.create_file(PAGE_NAME_2, PAGE_CONTENT_2)
        page_path_3 = self.create_file(PAGE_NAME_3, PAGE_CONTENT_3)
        page_path_4 = self.create_file(PAGE_NAME_4, PAGE_CONTENT_4)

        self.page_1 = Page(page_path_1, URL_1)
        self.page_2 = Page(page_path_2, URL_2)
        self.page_3 = Page(page_path_3, URL_3)
        self.page_4 = Page(page_path_4, URL_4)

    def test_highest_version_of_file(self):
        """
            Assert that get_highest_version_of_file_path gets the highest version for all paths
        """
        assert Page.get_highest_version_of_file_path(self.page_1.path) == self.page_1.path
        assert Page.get_highest_version_of_file_path(self.page_2.path) == self.page_3.path
        assert Page.get_highest_version_of_file_path(self.page_3.path) == self.page_3.path
        assert Page.get_highest_version_of_file_path(self.page_4.path) == self.page_4.path

    def test_filter_old_versions(self):
        """
            Assert that old versions are filtered from pages.
        """
        pages = [
            self.page_1,
            self.page_2,
            self.page_3,
            self.page_4
        ]

        filtered_pages = Page.filter_old_versions(pages)

        assert self.page_1 in filtered_pages
        assert self.page_2 not in filtered_pages
        assert self.page_3 in filtered_pages
        assert self.page_4 in filtered_pages

    def test_get_versions(self):
        """
            Assert that a path can get all versions
        """
        pages = [
            self.page_1,
            self.page_2,
            self.page_3,
            self.page_4
        ]

        pages_1 = Page.get_versions(self.page_1.path, pages)
        pages_2 = Page.get_versions(self.page_2.path, pages)
        pages_3 = Page.get_versions(self.page_3.path, pages)
        pages_4 = Page.get_versions(self.page_4.path, pages)

        assert self.page_1 in pages_1
        assert self.page_2 not in pages_1
        assert self.page_3 not in pages_1
        assert self.page_4 not in pages_1

        assert self.page_1 not in pages_2
        assert self.page_2 in pages_2
        assert self.page_3 in pages_2
        assert self.page_4 not in pages_2

        assert self.page_1 not in pages_3
        assert self.page_2 in pages_3
        assert self.page_3 in pages_3
        assert self.page_4 not in pages_3

        assert self.page_1 not in pages_4
        assert self.page_2 not in pages_4
        assert self.page_3 not in pages_4
        assert self.page_4 in pages_4

