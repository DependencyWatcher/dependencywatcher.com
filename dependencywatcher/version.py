#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

import re
from pkg_resources import parse_version

class Version(object):
	""" Version number parsing utilities """
	pattern = re.compile("([^\._-]+)\.?(\d+)?[\._-]?(.*)")

	REL_MAJOR = 1
	REL_MINOR = 2
	REL_BUGFIX = 3

	def __init__(self, text):
		self.text = text
		self.parsed = parse_version(text)
		m = self.pattern.match(text)
		if not m:
			raise Exception("Can't parse version: %s" % text)
		self.major = m.group(1)
		self.minor = m.group(2)
		self.bugfix = m.group(3)

	def __str__(self):
		return "Version \"%s\" <major: %s, minor: %s, bugfix: %s>" % \
			(self.text, self.major, self.minor, self.bugfix)

	def ensure_type(self, other):
		if not type(other) is Version:
			other = Version(other)
		return other

	def is_greater(self, other):
		return self.parsed > self.ensure_type(other).parsed

	def is_greater_or_equal(self, other):
		return self.parsed >= self.ensure_type(other).parsed

	def get_release_type(self, other):
		other = self.ensure_type(other)
		if self.major != other.major:
			return self.REL_MAJOR
		if self.minor != other.minor:
			return self.REL_MINOR
		if self.bugfix != other.bugfix:
			return self.REL_BUGFIX

