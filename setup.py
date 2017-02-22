#!/usr/bin/env python
#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from setuptools import setup, find_packages

setup(
	name="DependencyWatcher-Website",
	version="1.0",
	url="http://dependencywatcher.com",
	author="Michael Spector",
	author_email="michael@dependencywatcher.com",
	long_description=__doc__,
	packages=find_packages(),
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		"Flask>=0.10.1",
		"Flask-SQLAlchemy>=2.0",
		"Flask-Migrate",
		"Flask-Login>=0.3.0",
		"Flask-OAuth",
		"Flask-WTF",
		"sqlalchemy>=1.0.0b1",
		"bcrypt",
		"celery",
		"wtforms",
		"patool",
		"Pillow",
		"mailchimp",
		"python-slugify",
		"pyparsing",
                "reportlab>=3.2.0",
                "scandir"
	]
)
