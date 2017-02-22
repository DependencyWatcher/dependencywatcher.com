#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

class DBConf(object):
	""" Interface for accessing configuration stored in DB """

	@classmethod
	def load(cls):
		if not hasattr(cls, "config"):
			from dependencywatcher.website.model import Config
			from dependencywatcher.website.webapp import db
			cls.config = Config.query.one()
			db.session.expunge(cls.config)

	@classmethod
	def reload(cls):
		delattr(cls, "config")

	@classmethod
	def get(cls):
		cls.load()
		return cls.config

