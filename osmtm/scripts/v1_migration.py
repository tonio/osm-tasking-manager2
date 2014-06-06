#!env/bin/python
# -*- coding: utf-8 -*-

import transaction
import urllib
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.schema import (
    MetaData,
)

from sqlalchemy.exc import (
    IntegrityError
)

from osmtm.utils import (
    TileBuilder,
    max
)

from osmtm.models import (
    DBSession as session_v2,
    Area,
    Project,
    Task,
    License,
    User,
)

from sqlalchemy_i18n.manager import translation_manager

import shapely

from geoalchemy2 import (
    shape,
)
from geoalchemy2.functions import (
    ST_Transform,
)


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


def header(msg):
    print
    print bcolors.HEADER + "# " + msg + bcolors.ENDC


def success(msg):
    print bcolors.OKGREEN + msg + bcolors.ENDC


def failure(msg):
    print bcolors.FAIL + msg + bcolors.ENDC

translation_manager.options.update({
    'locales': ['en'],
    'get_locale_fallback': True
})


''' V1 '''
metadata_v1 = MetaData()
engine_v1 = create_engine('sqlite:///../../OSMTM.db')
session_v1 = sessionmaker(bind=engine_v1)()
metadata_v1.reflect(bind=engine_v1)

''' v2 '''
engine_v2 = create_engine('postgresql://www-data:www-data@localhost/osmtm')
session_v2.configure(bind=engine_v2)

jobs = metadata_v1.tables['jobs']
tiles = metadata_v1.tables['tiles']
tiles_history = metadata_v1.tables['tiles_history']
licenses = metadata_v1.tables['licenses']
users_table = metadata_v1.tables['users']

header("Cleaning up db")
with transaction.manager:
    # FIXME we may need to empty the V2 db first
    session_v2.query(Task).delete()
    session_v2.query(Project).delete()
    session_v2.query(Area).delete()
    session_v2.query(License).delete()
    session_v2.query(User).delete()
    session_v2.flush()

header("Retrieving users ids")
f = open('users.list', 'r+')
users = {}
for line in f:
    user = line.split(';')
    users[user[0]] = user[1]

print len(users)

for k, u in enumerate(session_v1.query(users_table).all()):
    username = u.username.encode('utf-8')
    if username not in users:
        print "%s - %s" % (k, u.username)
        url = "http://whosthat.osmz.ru/whosthat.php?action=names&q=%s" % \
            username
        response = urllib.urlopen(url)
        data = json.load(response)
        f.write('%s;' % username)

        found = False
        for user in data:
            if u.username in user["names"]:
                found = True
                f.write('%s' % user['id'])
                users[username] = user['id']

        if not found:
            f.write('%s' % -1)
            users[username] = -1

        f.write(';\n')
f.close()

print "%d users found" % len(users)

header("Importing users in v2")
# inverting users mapping, key is now id
users = {v: k for k, v in users.items()}

with transaction.manager:
    for id in users:
        username = users[id]
        if id != -1:
            user = User(id, username)
            session_v2.add(user)
    session_v2.flush()

success("%d users - successfully imported" % (len(users)))

header("Importing licenses")
with transaction.manager:
    query = session_v1.query(licenses).all()
    for l in query:
        license = License()
        license.id = l.id
        license.name = l.name
        license.description = l.description
        license.plain_text = l.plain_text
        session_v2.add(license)
        success("License %s - \"%s\" successfully imported" % (l.id, l.name))
    session_v2.flush()


header("Importing jobs and tasks")
with transaction.manager:
    for job in session_v1.query(jobs).filter(jobs.c.id).all():

        geometry = shapely.wkt.loads(job.geometry)
        geometry = ST_Transform(shape.from_shape(geometry, 3857), 4326)
        area = Area(geometry)
        session_v2.add(area)

        project = Project(job.title)
        project.id = job.id
        project.area = area
        project.zoom = job.zoom
        project.last_update = job.last_update
        project.description = job.description
        project.short_description = job.short_description
        project.private = job.is_private
        project.instructions = job.workflow
        project.imagery = job.imagery
        project.license_id = job.license_id

        tasks = []
        for tile in session_v1.query(tiles).filter(tiles.c.job_id == job.id).all():
            step = max / (2 ** (tile.zoom - 1))
            tb = TileBuilder(step)
            geometry = tb.create_square(tile.x, tile.y)
            geometry = ST_Transform(shape.from_shape(geometry, 3857), 4326)

            task = Task(tile.x, tile.y, tile.zoom, geometry)
            if tile.checkin == 1:
                task.state = Task.state_done
            elif tile.checkin == 2:
                task.state = Task.state_validated
            tasks.append(task)

        #for tile in session_v1.query(tiles_history).filter(tiles_history.c.job_id == job.id).all():
            #print tile

        project.tasks = tasks

        session_v2.add(project)
        session_v2.flush()
        success("Job %s - \"%s\" successfully imported" % (job.id, job.title))

    header("Updating projects done stats")
    for project in session_v2.query(Project).all():
        project.done = project.get_done()
        project.validated = project.get_validated()
    session_v2.flush()


    # FIXME reset the project id sequence
