#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from flask import Flask, request, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event
from urlparse import urlsplit
from datetime import datetime, date
from urllib import urlencode, quote
from dependencywatcher.db_conf import DBConf
import socket, os, sys

socket.setdefaulttimeout(10)

reload(sys)
sys.setdefaultencoding("utf-8")

app = Flask(__name__)
app.config.from_pyfile("../../config.py")
db = SQLAlchemy(app)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if app.config.get("SQLALCHEMY_DATABASE_URI").startswith("sqlite:"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

def url_for_page(page):
    args = request.view_args.copy()
    args["page"] = page
    url = url_for(request.endpoint, **args)
    if request.query_string:
        url = "%s?%s" % (url, request.query_string)
    return url

def feeling_lucky_url(term):
    return "http://www.google.com/webhp?#%s&btnI=I" % urlencode({"q": term})

def encodeURIComponent(str):
    return quote(str, safe="~()*!.'")

def plurify(number, single_form, many_form):
    return single_form if number == 1 else many_form

app.jinja_env.globals["config"] = DBConf.get
app.jinja_env.globals["url_for_page"] = url_for_page
app.jinja_env.globals["feeling_lucky_url"] = feeling_lucky_url
app.jinja_env.globals["encodeURIComponent"] = encodeURIComponent
app.jinja_env.globals["plurify"] = plurify
app.jinja_env.globals["urlsplit"] = urlsplit

import dependencywatcher.website.views.pages
import dependencywatcher.website.views.login
import dependencywatcher.website.views.profile
import dependencywatcher.website.views.dashboard
import dependencywatcher.website.views.repository
import dependencywatcher.website.views.github
import dependencywatcher.website.views.bitbucket
import dependencywatcher.website.views.tasks
import dependencywatcher.website.views.alerts
import dependencywatcher.website.views.api
import dependencywatcher.website.views.setup
import dependencywatcher.website.views.reference
try:
    import dependencywatcher.website.views.upgrade
    import dependencywatcher.website.views.blog
except ImportError:
    pass

