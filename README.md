# OpenStreetMap Tasking Manager

[![Build Status](https://travis-ci.org/hotosm/osm-tasking-manager2.svg?branch=master)](https://travis-ci.org/hotosm/osm-tasking-manager2)
[![Coverage Status](https://coveralls.io/repos/hotosm/osm-tasking-manager2/badge.png?branch=master)](https://coveralls.io/r/hotosm/osm-tasking-manager2?branch=master)

## About

OSMTM enables collaborative work on specific areas in OpenStreetMap by defining
clear workflows to be achieved and by breaking tasks down into pieces.

The application is written in Python using the Pyramid framework.

This is the 2.0 version of the Tasking Manager.

## Installation

First clone the git repository:

    git clone --recursive git://github.com/hotosm/osm-tasking-manager2.git

Installing OSMTM in a Virtual Python environment is recommended.

To create a virtual Python environment:

    cd osm-tasking-manager2
    sudo easy_install virtualenv
    virtualenv --no-site-packages env
    env/bin/python setup.py develop

*Tip: if you encounter problems installing `psycopg2` especially on Mac, it is recommended to follow advice proposed [here](http://stackoverflow.com/questions/22313407/clang-error-unknown-argument-mno-fused-madd-python-package-installation-fa).*

### Database

OSMTM requires a PostgreSQL/PostGIS database. Version 2.x of PostGIS is
required.

First create a database user/role named `www-data`:

    sudo -u postgres createuser -SDRP www-data

Then create a database named `osmtm`:

    sudo -u postgres createdb -O www-data osmtm
    sudo -u postgres psql -d osmtm -c "CREATE EXTENSION postgis;"

You're now ready to do the initial population of the database. An
`initialize_osmtm_db` script is available in the virtual env for that:

    env/bin/initialize_osmtm_db

### Local settings

You certainly will need some local specific settings, like the db user or
password. For this, you can create a `local.ini` file in the project root,
where you can then override every needed setting.
For example:

    [app:main]
    sqlalchemy.url = postgresql://www-data:www-data@localhost/osmtm

Note: you can also put your local settings file anywhere else on your
file system, and then create a `LOCAL_SETTINGS_PATH` environment variable
to make the project aware of this.

## Launch the application

    env/bin/pserve --reload development.ini

## Styles

The CSS stylesheet are compiled using less. Launch the following command as
soon as you change the css::

    lessc -ru osmtm/static/css/main.less > osmtm/static/css/main.css

## Tests

The tests use a separate database. Create that database first:

    sudo -u postgres createdb -O www-data osmtm_tests
    sudo -u postgres psql -d osmtm_tests -c "CREATE EXTENSION postgis;"

Create a `local.test.ini`file in the project root, where you will add the
settings for the database connection.
For example:

    [app:main]
    sqlalchemy.url = postgresql://www-data:www-data@localhost/osmtm_tests

To run the tests, use the following command:

    env/bin/nosetests

## Upgrading

When upgrading the application code, you may need to upgrade the database
as well in case the schema has changed.

In order to do you this, you first need to ensure that you'll be able to
re-create the database in case something wents wrong. Creating a copy of the
current data is a good idea.

Then you can run the following command:

    env/bin/alembic upgrade head
