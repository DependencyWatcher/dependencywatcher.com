#!/usr/bin/env python2.7
#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from flask.ext.script import Server, Manager
from flask.ext.migrate import Migrate, MigrateCommand
from dependencywatcher.website.webapp import app, db

def create_app(loglevel):
	if loglevel is not None:
		import logging
		logging.basicConfig(level=getattr(logging, loglevel))
	return app

migrate = Migrate(app, db)
manager = Manager(create_app)
manager.add_command("runserver", Server(port=3001, host="0.0.0.0"))
manager.add_command("db", MigrateCommand)
manager.add_option("-l", "--loglevel", dest="loglevel", required=False)

if __name__ == "__main__":
	manager.run()

