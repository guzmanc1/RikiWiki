"""
    Wiki core
    ~~~~~~~~~
"""
from collections import OrderedDict
from io import open
import os
import re

from flask import abort
from flask import url_for
import markdown
import ntpath

def clean_url(url):
    """
        Cleans the url and corrects various errors. Removes multiple
        spaces and all leading and trailing spaces. Changes spaces
        to underscores and makes all characters lowercase. Also
        takes care of Windows style folders use.

        :param str url: the url to clean


        :returns: the cleaned url
        :rtype: str
    """
    url = re.sub('[ ]{2,}', ' ', url).strip()
    url = url.lower().replace(' ', '_')
    url = url.replace('\\\\', '/').replace('\\', '/')
    return url


def wikilink(text, url_formatter=None):
    """
        Processes Wikilink syntax "[[Link]]" within the html body.
        This is intended to be run after content has been processed
        by markdown and is already HTML.

        :param str text: the html to highlight wiki links in.
        :param function url_formatter: which URL formatter to use,
            will by default use the flask url formatter

        Syntax:
            This accepts Wikilink syntax in the form of [[WikiLink]] or
            [[url/location|LinkName]]. Everything is referenced from the
            base location "/", therefore sub-pages need to use the
            [[page/subpage|Subpage]].

        :returns: the processed html
        :rtype: str
    """
    if url_formatter is None:
        url_formatter = url_for
    link_regex = re.compile(
        r"((?<!\<code\>)\[\[([^<].+?) \s*([|] \s* (.+?) \s*)?]])",
        re.X | re.U
    )
    for i in link_regex.findall(text):
        title = [i[-1] if i[-1] else i[1]][0]
        url = clean_url(i[1])
        html_url = u"<a href='{0}'>{1}</a>".format(
            url_formatter('wiki.display', url=url),
            title
        )
        text = re.sub(link_regex, html_url, text, count=1)
    return text


class Processor(object):
    """
        The processor handles the processing of file content into
        metadata and markdown and takes care of the rendering.

        It also offers some helper methods that can be used for various
        cases.
    """

    preprocessors = []
    postprocessors = [wikilink]

    def __init__(self, text):
        """
            Initialization of the processor.

            :param str text: the text to process
        """
        self.md = markdown.Markdown([
            'codehilite',
            'fenced_code',
            'meta',
            'tables'
        ])
        self.input = text
        self.markdown = None
        self.meta_raw = None

        self.pre = None
        self.html = None
        self.final = None
        self.meta = None

    def process_pre(self):
        """
            Content preprocessor.
        """
        current = self.input
        for processor in self.preprocessors:
            current = processor(current)
        self.pre = current

    def process_markdown(self):
        """
            Convert to HTML.
        """
        self.html = self.md.convert(self.pre)


    def split_raw(self):
        """
            Split text into raw meta and content.
        """
        self.meta_raw, self.markdown = self.pre.split('\n\n', 1)

    def process_meta(self):
        """
            Get metadata.

            .. warning:: Can only be called after :meth:`html` was
                called.
        """
        # the markdown meta plugin does not retain the order of the
        # entries, so we have to loop over the meta values a second
        # time to put them into a dictionary in the correct order
        self.meta = OrderedDict()
        for line in self.meta_raw.split('\n'):
            key = line.split(':', 1)[0]
            # markdown metadata always returns a list of lines, we will
            # reverse that here
            self.meta[key.lower()] = \
                '\n'.join(self.md.Meta[key.lower()])

    def process_post(self):
        """
            Content postprocessor.
        """
        current = self.html
        for processor in self.postprocessors:
            current = processor(current)
        self.final = current

    def process(self):
        """
            Runs the full suite of processing on the given text, all
            pre and post processing, markdown rendering and meta data
            handling.
        """
        self.process_pre()
        self.process_markdown()
        self.split_raw()
        self.process_meta()
        self.process_post()

        return self.final, self.markdown, self.meta


class Page(object):
    def __init__(self, path, url, new=False):
        self.path = path
        self.url = url
        self._meta = OrderedDict()
        if not new:
            self.load()
            self.render()

    def __repr__(self):
        return u"<Page: {}@{}>".format(self.url, self.path)

    def load(self):
        with open(self.path, 'r', encoding='utf-8') as f:
            self.content = f.read()

    def render(self):
        processor = Processor(self.content)
        self._html, self.body, self._meta = processor.process()

    @staticmethod
    def get_filename_from_path(path):
        """
        @file: core.py
        @author: Dustin Gulley
        @date: 04/08/2018
        returns the filename from a given path
        'path/to/file/myfile.txt' -> 'myfile.txt'
        """
        return ntpath.basename(path)

    @staticmethod
    def get_path_without_filename(path):
        """
        @file: core.py
        @author: Dustin Gulley
        @date: 04/08/2018
        returns the filename from a given path
        'path/to/file/myfile.txt' -> 'path/to/file'
        """
        return ntpath.dirname(path)

    @staticmethod
    def __split_filename_from_extension(filename):
        """
        @file: core.py
        @author: Dustin Gulley
        @date: 04/08/2018
        Separates the filename from the extension, returns a pair
        'myfile.txt' -> ['myfile', 'txt']
        """
        return filename.rsplit('.', 1)

    @staticmethod
    def __get_filename_without_version(filename):
        """
        @file: core.py
        @author: Dustin Gulley
        @date: 04/08/2018
        Expects an extensionless filename and removes _v# from the end
        'myfile_v1' -> 'myfile'
        """
        return re.sub(r'_v\d+$', '', filename)

    @staticmethod
    def __get_all_versions_of_unversioned_file(path, unversioned_filename, ext):
        """
        @file: core.py
        @author: Dustin Gulley
        @date: 04/08/2018
        Gets all versions of a file
        'myfile' -> ['path/to/myfile_v1.txt', 'path/to/myfile_v2.txt']
        """
        files_to_return = []
        for root, dirs, files in os.walk(path):
            for f in files:
                temp = f.replace(unversioned_filename, '', 1)   # Remove the filename
                temp = temp.replace('.' + ext, '')              # Remove the extension
                if re.match(r'^_v\d+$', temp):                  # Only the version should be left
                    files_to_return.append(f)
        return files_to_return

    @staticmethod
    def __get_filename_without_extension(filepath):
        """
        @file: core.py
        @author: Dustin Gulley
        @date: 04/08/2018
        Expects a path with a filename and returns a file without the ext
        'path/to/myfile.txt' - > 'myfile'
        """
        filename = Page.get_filename_from_path(filepath)
        filenamename_ext = Page.__split_filename_from_extension(filename)
        return filenamename_ext[0]

    @staticmethod
    def __get_version_from_filename(filename):
        """
        @file: core.py
        @author: Dustin Gulley
        @date: 04/08/2018
        Expects a filename without
        'myfile_v1.txt' - > 1
        """
        temp_file = Page.__get_filename_without_extension(filename)
        version = re.findall('^.*([0-9]+)$', temp_file)

        if len(version) == 0:
            return 0
        else:
            return int(version[0])

        return version

    @staticmethod
    def __get_highest_version_number(file_list):
        """
        @file: core.py
        @author: Dustin Gulley
        @date: 04/08/2018
        Returns highest version from a list of files, 0 if no version exists
        ['path/to/myfile_v1.txt', path/to/myfile_v2.txt] -> 2
        """
        version = 0
        for f in file_list:
            temp_version = Page.__get_version_from_filename(f)
            if temp_version > version:
                version = temp_version
        return version

    @staticmethod
    def __get_all_versions_of_file(file_path):
        """
        @file: core.py
        @author: Dustin Gulley
        @date: 04/08/2018
        Returns all versions of a file
        'path/to/myfile_v2.txt' -> ['path/to/myfile_v1.txt', path/to/myfile_v2.txt]
        """
        file_path_without_file = Page.get_path_without_filename(file_path)
        filename = Page.get_filename_from_path(file_path)
        filename_ext = Page.__split_filename_from_extension(filename)
        unversioned_filename = Page.__get_filename_without_version(filename_ext[0])
        return Page.__get_all_versions_of_unversioned_file(file_path_without_file, unversioned_filename, filename_ext[1])

    @staticmethod
    def __get_highest_version_number_from_file_path(file_path):
        """
        @file: core.py
        @author: Dustin Gulley
        @date: 04/08/2018
        Returns highest version from a file path, 0 if no version exists
        'path/to/myfile_v1.txt' -> 2
        """
        all_versions = Page.__get_all_versions_of_file(file_path)
        return Page.__get_highest_version_number(all_versions)

    @staticmethod
    def get_highest_version_of_file_path(file_path):
        """
        @file: core.py
        @author: Dustin Gulley
        @date: 04/08/2018
        Returns highest version from a file path, 0 if no version exists
        'path/to/myfile_v1.txt' -> 'path/to/myfile_v2.txt'
        """
        version = Page.__get_highest_version_number_from_file_path(file_path)
        path = Page.get_path_without_filename(file_path)
        filename = Page.get_filename_from_path(file_path)
        filename_ext = Page.__split_filename_from_extension(filename)
        filename_no_version = Page.__get_filename_without_version(filename_ext[0])

        if version > 0:
            return path + "/" + filename_no_version + '_v' + str(version) + '.' + filename_ext[1]
        else:
            return file_path

    @staticmethod
    def filter_old_versions(pages):
        """
        @file: core.py
        @author: Dustin Gulley
        @date: 04/08/2018
        Returns highest version from a file path, 0 if no version exists
        [Page with 'path/to/myfile_v1.txt', Page with 'path/to/myfile_v2.txt'] -> [Page with 'path/to/myfile_v2.txt']
        """
        pages_to_return = []
        for page in pages:
            p = page.get_highest_version_of_file_path(page.path)
            if p == page.path:
                if page not in pages_to_return:
                    pages_to_return.append(page)

        return pages_to_return

    @staticmethod
    def get_versions(filepath, all_versions):
        """
        @file: routes.py
        @author: Dustin Gulley
        @date: 04/08/2018
        Filters out all files that aren't a version of the filepath
        'path/to/myfile_v1.txt',
        [Page with 'path/to/myfile_v1.txt', Page with 'path/to/myfile_v2.txt', Page with 'path/to/myfile2_v1.txt']
        -> [Page with 'path/to/myfile_v1.txt', Page with 'path/to/myfile_v2.txt']
        """
        versions = Page.__get_all_versions_of_file(filepath)
        path = Page.get_path_without_filename(filepath)
        pages = []
        for version in versions:
            for v in all_versions:
                if path + '/' + version == v.path:
                    pages.append(v)
        return pages

    def save(self, update=True):
        folder = os.path.dirname(self.path)

        version = Page.__get_highest_version_number_from_file_path(self.path)  # Gets the highest version
        version = version + 1
        dirname = Page.get_path_without_filename(self.path)
        filename = Page.get_filename_from_path(self.path)
        filename_ext = Page.__split_filename_from_extension(filename)
        filename = Page.__get_filename_without_version(filename_ext[0])

        self.path = dirname + '/' + filename + '_v' + str(version) + '.' + filename_ext[1]

        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(self.path, 'w', encoding='utf-8') as f:
            for key, value in self._meta.items():
                line = u'%s: %s\n' % (key, value)
                f.write(line)
            f.write(u'\n')
            f.write(self.body.replace(u'\r\n', u'\n'))
        if update:
            self.load()
            self.render()

    @property
    def meta(self):
        return self._meta

    def __getitem__(self, name):
        return self._meta[name]

    def __setitem__(self, name, value):
        self._meta[name] = value

    @property
    def html(self):
        return self._html

    def __html__(self):
        return self.html

    @property
    def title(self):
        try:
            return self['title']
        except KeyError:
            return self.url

    @title.setter
    def title(self, value):
        self['title'] = value

    @property
    def tags(self):
        try:
            return self['tags']
        except KeyError:
            return ""

    @tags.setter
    def tags(self, value):
        self['tags'] = value


class Wiki(object):
    def __init__(self, root):
        self.root = root

    def path(self, url):
        return os.path.join(self.root, url + '.md')

    def exists(self, url):
        path = self.path(url)
        return os.path.exists(path)

    def get(self, url):
        path = self.path(url)
        #path = os.path.join(self.root, url + '.md')
        if self.exists(url):
            return Page(path, url)
        return None

    def get_or_404(self, url):
        page = self.get(url)
        if page:
            return page
        abort(404)

    def get_bare(self, url):
        path = self.path(url)
        if self.exists(url):
            return False
        return Page(path, url, new=True)

    def move(self, url, newurl):
        source = os.path.join(self.root, url) + '.md'
        target = os.path.join(self.root, newurl) + '_v1.md'
        # normalize root path (just in case somebody defined it absolute,
        # having some '../' inside) to correctly compare it to the target
        root = os.path.normpath(self.root)

        # get root path longest common prefix with normalized target path
        common = os.path.commonprefix((root, os.path.normpath(target)))
        # common prefix length must be at least as root length is
        # otherwise there are probably some '..' links in target path leading
        # us outside defined root directory
        if len(common) < len(root):
            raise RuntimeError(
                'Possible write attempt outside content directory: '
                '%s' % newurl)
        # create folder if it does not exists yet
        folder = os.path.dirname(target)
        if not os.path.exists(folder):
            os.makedirs(folder)
        os.rename(source, target)

    def delete(self, url):
        path = self.path(url)
        if not self.exists(url):
            return False
        os.remove(path)
        return True

    def index(self):
        """
            Builds up a list of all the available pages.

            :returns: a list of all the wiki pages
            :rtype: list
        """
        # make sure we always have the absolute path for fixing the
        # walk path
        pages = []
        root = os.path.abspath(self.root)
        for cur_dir, _, files in os.walk(root):
            # get the url of the current directory
            cur_dir_url = cur_dir[len(root)+1:]
            for cur_file in files:
                path = os.path.join(cur_dir, cur_file)
                if cur_file.endswith('.md'):
                    url = clean_url(os.path.join(cur_dir_url, cur_file[:-3]))
                    page = Page(path, url)
                    pages.append(page)
        return sorted(pages, key=lambda x: x.title.lower())

    def index_by(self, key):
        """
            Get an index based on the given key.

            Will use the metadata value of the given key to group
            the existing pages.

            :param str key: the attribute to group the index on.

            :returns: Will return a dictionary where each entry holds
                a list of pages that share the given attribute.
            :rtype: dict
        """
        pages = {}
        for page in self.index():
            value = getattr(page, key)
            pre = pages.get(value, [])
            pages[value] = pre.append(page)
        return pages

    def get_by_title(self, title):
        pages = self.index(attr='title')
        return pages.get(title)

    def get_tags(self):
        pages = self.index()
        tags = {}
        for page in pages:
            pagetags = page.tags.split(',')
            for tag in pagetags:
                tag = tag.strip()
                if tag == '':
                    continue
                elif tags.get(tag):
                    tags[tag].append(page)
                else:
                    tags[tag] = [page]
        return tags

    def index_by_tag(self, tag):
        pages = self.index()
        tagged = []
        for page in pages:
            if tag in page.tags:
                tagged.append(page)
        return sorted(tagged, key=lambda x: x.title.lower())

    def search(self, term, ignore_case=True, attrs=['title', 'tags', 'body']):
        pages = self.index()
        regex = re.compile(term, re.IGNORECASE if ignore_case else 0)
        matched = []
        for page in pages:
            for attr in attrs:
                if regex.search(getattr(page, attr)):
                    matched.append(page)
                    break
        return matched
