#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from flask import request, redirect, url_for, abort, Response
from flask.ext.login import LoginManager, current_user, login_user
from dependencywatcher.website.model import *
from dependencywatcher.website.webapp import app, db
from functools import wraps
import json

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

def requires_roles(*roles):
	def wrapper(f):
		@wraps(f)
		def wrapped(*args, **kwargs):
			if current_user is None or not current_user.is_authenticated \
				or not current_user.has_roles(*roles):
				abort(403)
			return f(*args, **kwargs)
		return wrapped
	return wrapper

@login_manager.user_loader
def load_user(id):
	try:
		return User.query.get(id)
	except:
		return None

@login_manager.request_loader
def load_user_from_request(request):
	api_key = request.headers.get("Authorization")
	if api_key:
		api_key = api_key.replace("apikey=", "", 1)
		try:
			return User.query.filter_by(api_key=api_key).first()
		except:
			pass
	return None

@login_manager.unauthorized_handler
def unauthorized():
	if request.path.startswith("/api/"):
		response = Response(u"Invalid API key", status=401)
		response.headers["WWW-Authenticate"] = "Basic \"api\""
		return response
	return redirect("%s?next=%s" % (url_for("login"), request.path))

class OAuthLogin(object):
	def __init__(self, oauth_attr_name, oauth_data):
		self.oauth_attr_name = oauth_attr_name
		self.oauth_data = oauth_data

	def find_existing_user(self):
		raise NotImplementedError

	def get_remote_email(self):
		raise NotImplementedError

	def get_remote_display_name(self):
		raise NotImplementedError

	def get_remote_avatar(self):
		raise NotImplementedError

	def update_user_oauth_data(self, user):
		""" Updates stored OAuth data if needed """
		stored_data = getattr(user, self.oauth_attr_name)
		current_data = json.dumps(self.oauth_data)
		if stored_data != current_data:
			setattr(user, self.oauth_attr_name, current_data)
			return True
		return False

	def login(self):
		user = self.find_existing_user()
		if not user is None:
			# Check if user needs update for his stored OAuth data:
			if self.update_user_oauth_data(user):
				# Just in case, activate the account:
				user.activate()
			user.purge_repositories()
		else:
			user = User()
			user.email = self.get_remote_email()
			user.name = self.get_remote_display_name()

			avatar_url = self.get_remote_avatar()
			user.update_avatar(url=avatar_url) if avatar_url else user.find_avatar()

			self.update_user_oauth_data(user)
			db.session.add(user)

			user.perform_new_user_actions()

		db.session.commit()
		login_user(user)

	def handle_callback(self):
		if current_user.is_authenticated:
			if self.update_user_oauth_data(current_user):
				db.session.commit()
		else:
			self.login()

