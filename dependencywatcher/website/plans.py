#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

class Plan(object):
	""" Service usage plans and rules based on them """
	DEVELOPER = 1
	COMPANY = 2
	ENTERPRISE = 3
	ON_PREMISE = 4

	def __init__(self, type, max_public_repos=0, max_private_repos=0, monthly_price=0):
		self.type = type
		self.max_public_repos = max_public_repos
		self.max_private_repos = max_private_repos
		self.monthly_price = monthly_price

	def can_add_public_repo(self, user):
		if self.type == Plan.ON_PREMISE:
			return True
		return self.get_public_usage(user) < self.max_public_repos

	def can_add_private_repo(self, user):
		if self.type == Plan.ON_PREMISE:
			return True
		return self.get_private_usage(user) < self.max_private_repos

	def can_add_repo(self, user, repo):
		if self.type == Plan.ON_PREMISE:
			return True
		if not repo.private:
			return self.can_add_public_repo(user)
		return self.can_add_private_repo(user)

	def get_public_usage(self, user):
		return len([r for r in user.get_repositories() if not r.private])

	def get_private_usage(self, user):
		return len([r for r in user.get_repositories() if r.private])

	@staticmethod
	def by_type(type):
		if type == Plan.ENTERPRISE:
			return Plan(type, 100, 20, 50)
		if type == Plan.COMPANY:
			return Plan(type, 20, 5, 5)
		if type == Plan.DEVELOPER:
			return Plan(type, 5, 1)
		if type == Plan.ON_PREMISE:
			return Plan(type)
		return None

	def to_name(self):
		if self.type == Plan.ENTERPRISE:
			return "Enterprise"
		if self.type == Plan.COMPANY:
			return "Company"
		if self.type == Plan.DEVELOPER:
			return "Developer"
		if self.type == Plan.ON_PREMISE:
			return "On-Premise"
		return "Unknown"

class PlanException(Exception):
	""" This exception is thrown when current plan doesn't allow to execute an operation """
	pass

