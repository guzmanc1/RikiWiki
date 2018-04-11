"""
    Routes
    ~~~~~~
"""
from flask import Blueprint
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user
from user import UserManager

from wiki.core import Processor
from wiki.web.forms import EditorForm
from wiki.web.forms import LoginForm
from wiki.web.forms import SearchForm
from wiki.web.forms import URLForm
from wiki.web.forms import CreateUserForm
from wiki.web import current_wiki
from wiki.web import current_users
from wiki.web.user import protect
from wiki.core import Page


bp = Blueprint('wiki', __name__)

@bp.route('/')
@protect
def home():
    pages = current_wiki.index()
    page = Page.get_highest_page_from_unversioned_file(pages, 'home')
    # page = current_wiki.get('home')
    if page:
        return display(page.url)
    return render_template('home.html')

@bp.route('/index/')
@protect
def index():
    pages = current_wiki.index()
    pages = Page.filter_old_versions(pages)
    return render_template('index.html', pages=pages)


@bp.route('/<path:url>/')
@protect
def display(url):
    page = current_wiki.get_or_404(url)
    return render_template('page.html', page=page)

@bp.route('/display_version/<path:url>/')
@protect
def display_version(url):
    """
    @file: routes.py
    @author: Dustin Gulley
    @date: 04/08/2018
    Similar to display but with only conditions applying to a previous version
    """
    page = current_wiki.get_or_404(url)
    return render_template('versioned_page.html', page=page)

@bp.route('/recover/<path:url>/')
@protect
def recover(url):
    """
    @file: routes.py
    @author: Dustin Gulley
    @date: 04/08/2018
    Sets the page corresponding to the url as the newest version
    """
    page = current_wiki.get_or_404(url)
    form = EditorForm(obj=page)
    if not page:
        page = current_wiki.get_bare(url)
    form.populate_obj(page)
    page.save()
    flash('"%s" was saved.' % page.title, 'success')
    return redirect(url_for('wiki.display', url=url))


@bp.route('/create/', methods=['GET', 'POST'])
@protect
def create():
    form = URLForm()
    if form.validate_on_submit():
        return redirect(url_for(
            'wiki.edit', url=form.clean_url(form.url.data)))
    return render_template('create.html', form=form)


@bp.route('/edit/<path:url>/', methods=['GET', 'POST'])
@protect
def edit(url):
    page = current_wiki.get(url)
    form = EditorForm(obj=page)
    if form.validate_on_submit():
        if not page:
            page = current_wiki.get_bare(url)
        form.populate_obj(page)
        page.save()
        new_path = Page.get_highest_version_of_file_path(page.path)
        pages = current_wiki.index()
        new_page = None

        for p in pages:
            if p.path == new_path:
                new_page = p

        if p is None:
            new_page = page

        flash('"%s" was saved.' % new_page.title, 'success')
        return redirect(url_for('wiki.display', url=new_page.url))
    return render_template('editor.html', form=form, page=page)


@bp.route('/versions/<path:url>/', methods=['GET', 'POST'])
@protect
def versions(url):
    """
    @file: routes.py
    @author: Dustin Gulley
    @date: 04/08/2018
    Returns all page versions of a specified url
    'myfile_v1' -> [Page with 'path/to/myfile_v1.txt', Page with 'path/to/myfile_v2.txt']
    """
    page = current_wiki.get(url)
    all_pages = current_wiki.index()
    pages = Page.get_versions(page.path, all_pages)
    return render_template('versions.html', pages=pages)


@bp.route('/preview/', methods=['POST'])
@protect
def preview():
    data = {}
    processor = Processor(request.form['body'])
    data['html'], data['body'], data['meta'] = processor.process()
    return data['html']


@bp.route('/move/<path:url>/', methods=['GET', 'POST'])
@protect
def move(url):
    page = current_wiki.get_or_404(url)
    form = URLForm(obj=page)
    if form.validate_on_submit():
        newurl = form.url.data
        current_wiki.move(url, newurl)

        # Delete non-moved pages
        all_pages = current_wiki.index()
        pages = Page.get_versions(page.path, all_pages)

        for p in pages:
            current_wiki.delete(p.url)

        flash('Page "%s" was deleted.' % page.title, 'success')


        return redirect(url_for('wiki.display', url=newurl))
    return render_template('move.html', form=form, page=page)


@bp.route('/delete/<path:url>/')
@protect
def delete(url):
    page = current_wiki.get_or_404(url)
    all_pages = current_wiki.index()
    pages = Page.get_versions(page.path, all_pages)

    for p in pages:
        current_wiki.delete(p.url)

    flash('Page "%s" was deleted.' % page.title, 'success')
    return redirect(url_for('wiki.home'))


@bp.route('/tags/')
@protect
def tags():
    ts = current_wiki.get_tags()
    new_tags = {}
    for t in ts:
        if t not in new_tags:
            new_tags[t] = []
        for p in ts[t]:
            page = Page.get_highest_version_of_file_path(p.path)
            if page not in new_tags[t]:
                new_tags[t].append(page)

    return render_template('tags.html', tags=new_tags)


@bp.route('/tag/<string:name>/')
@protect
def tag(name):
    tagged = current_wiki.index_by_tag(name)
    new_pages = []

    for t in tagged:
        p = Page.get_highest_version_of_file_path(t.path)
        if t.path == p and t not in new_pages:
            new_pages.append(t)

    return render_template('tag.html', pages=new_pages, tag=name)


@bp.route('/search/', methods=['GET', 'POST'])
@protect
def search():
    form = SearchForm()
    if form.validate_on_submit():
        results = current_wiki.search(form.term.data, form.ignore_case.data)
        results = Page.filter_old_versions(results)
        return render_template('search.html', form=form,
                               results=results, search=form.term.data)
    return render_template('search.html', form=form, search=None)


@bp.route('/user/login/', methods=['GET', 'POST'])
def user_login():
    form = LoginForm()
    if form.validate_on_submit():
        user = current_users.get_user(form.name.data)
        login_user(user)
        user.set('authenticated', True)
        flash('Login successful.', 'success')
        return redirect(request.args.get("next") or url_for('wiki.index'))
    return render_template('login.html', form=form)


@bp.route('/user/logout/')
@login_required
def user_logout():
    current_user.set('authenticated', False)
    logout_user()
    flash('Logout successful.', 'success')
    return redirect(url_for('wiki.index'))


@bp.route('/user/')
def user_index():
    pass


@bp.route('/user/create/', methods=['GET', 'POST'])
def user_create():
    form = CreateUserForm()
    manager = UserManager('user')
    if form.validate_on_submit():
        manager.add_user(form.name.data, form.password.data, True, [], None)
        user = current_users.get_user(form.name.data)
        login_user(user)
        user.set('authenticated', True)
        flash('User successfully created', 'success')
        return redirect(url_for('wiki.index'))
    return render_template('createuser.html', form=form)


@bp.route('/user/<int:user_id>/')
def user_admin(user_id):
    pass


@bp.route('/user/delete/<int:user_id>/')
def user_delete(user_id):
    pass


"""
    Error Handlers
    ~~~~~~~~~~~~~~
"""


@bp.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

