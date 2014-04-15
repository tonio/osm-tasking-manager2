from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPUnauthorized

from sqlalchemy import (
    desc,
    asc,
    or_,
)

from ..models import (
    DBSession,
    Project,
    User,
)

from webhelpers.paginate import (
    PageURL_WebOb,
    Page
)

from .task import check_task_expiration

from pyramid.security import authenticated_userid


@view_config(route_name='home', renderer='home.mako')
def home(request):
    check_task_expiration()

    # no user in the DB yet
    if DBSession.query(User.username).count() == 0:   # pragma: no cover
        request.override_renderer = 'start.mako'
        return dict(page_id="start")

    query = DBSession.query(Project)

    user_id = authenticated_userid(request)
    user = None
    if user_id is not None:
        user = DBSession.query(User).get(user_id)

    if not user:
        query = query.filter(Project.private == False)  # noqa
    elif not user.admin:
        query = query.outerjoin(Project.allowed_users)
        filter = or_(Project.private == False,  # noqa
                     User.id == user_id)
        query = query.filter(filter)

    sort_by = 'project.%s' % request.params.get('sort_by', 'id')
    direction = request.params.get('direction', 'asc')
    if direction == 'desc':
        sort_by = desc(sort_by)
    else:
        sort_by = asc(sort_by)

    query = query.order_by(sort_by)
    projects = query.all()

    page = int(request.params.get('page', 1))
    page_url = PageURL_WebOb(request)
    paginator = Page(projects, page, url=page_url, items_per_page=2)

    return dict(page_id="home", projects=projects, paginator=paginator)


@view_config(route_name="user_prefered_editor", renderer='json')
def user_prefered_editor(request):
    editor = request.matchdict['editor']
    request.response.set_cookie('prefered_editor', value=editor,
                                max_age=20 * 7 * 24 * 60 * 60)

    return dict()


@view_config(route_name="user_prefered_language", renderer='json')
def user_prefered_language(request):
    language = request.matchdict['language']
    request.response.set_cookie('_LOCALE_', value=language,
                                max_age=20 * 7 * 24 * 60 * 60)
    return dict()


@view_config(context='pyramid.httpexceptions.HTTPUnauthorized')
def unauthorized(request):
    if request.is_xhr:
        return HTTPUnauthorized()
    return HTTPFound(request.route_path('login',
                                        _query=[('came_from', request.url)]))
