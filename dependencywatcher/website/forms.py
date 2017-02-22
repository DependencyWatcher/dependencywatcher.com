#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from dependencywatcher.website.model import *
from dependencywatcher.website.ldap_login import LDAP_Login
from dependencywatcher.website.webapp import db
from dependencywatcher.db_conf import DBConf
from flask.ext.login import current_user
from flask.ext.wtf import Form
from wtforms.ext.sqlalchemy.orm import model_form
from wtforms import fields, validators
import urllib

class LoginForm(Form):
	email = fields.TextField(u"Email Address", validators=[validators.Email()])
	password = fields.PasswordField(u"Password", validators=[validators.Required()])

	def validate(self):
		if not Form.validate(self):
			return False
		user = User.query.filter_by(email=self.email.data).first()
		if user is not None and not user.is_ldap:
			if not user.is_active():
				self.email.errors.append(u"""This account was not activated.
					<a href='/activate/request/%s' class='alert-link'>Send</a> activation link again.""" % urllib.quote(self.email.data))
				return False
			if user.check_password(self.password.data):
				self.user = user
				return True
		else:
			if DBConf.get().ldap_enabled:
				self.user = LDAP_Login().login(self.email.data, self.password.data)
				if self.user is not None:
					return True
		self.password.errors.append(u"Wrong email or password")
		return False

class PasswordResetForm(Form):
	password = fields.PasswordField(u"Password", validators=[validators.Required(), validators.EqualTo("cpassword", message=u"Passwords do not match")])
	cpassword = fields.PasswordField(u"Password Confirmation")

class SignupForm(PasswordResetForm):
	email = fields.TextField(u"Email Address", validators=[validators.Email()])
	name = fields.TextField(u"Full Name", validators=[validators.Required()])

	def validate(self):
		if not super(SignupForm, self).validate():
			return False
		if User.query.filter_by(email=self.email.data).count() > 0:
			self.email.errors.append(u"This email address is already registered")
			return False
		return True

class ProfileAccountForm(Form):
	password = fields.PasswordField(u"Password", validators=[validators.EqualTo("cpassword", message=u"Passwords do not match")])
	cpassword = fields.PasswordField(u"Password Confirmation")
	name = fields.TextField(u"Full Name")
	email = fields.TextField(u"Email Address", validators=[validators.Email()])
	image = fields.FileField(u"User Picture")

	def validate(self):
		if not Form.validate(self):
			return False
		if self.email.data != current_user.email and User.query.filter_by(email=self.email.data).count() > 0:
			self.email.errors.append(u"This email address is registered")
			return False
		return True

RepositoryImportForm = model_form(Repository, base_class=Form, db_session=db.session)
BlogPostForm = model_form(BlogPost, base_class=Form, db_session=db.session)
UserSettingsForm = model_form(UserSettings, base_class=Form, db_session=db.session)

class RepositoryUploadForm(Form):
	name = fields.TextField(u"Repository Name", validators=[validators.Required()])
	file = fields.FileField(u"Source Code Archive")
	update = fields.HiddenField()

	def validate(self):
		if not Form.validate(self):
			return False
		if self.update.data != "true" and current_user.has_repository(self.name.data):
			self.name.errors.append(u"Repository with such name already uploaded. Please choose another name.")
			return False
		return True

class SetupWebsiteForm(Form):
	site_url = fields.TextField(u"Website URL", validators=[validators.URL(require_tld=False)])
	workdir = fields.TextField(u"Working Directory", validators=[validators.Required()])
	request_activation = fields.BooleanField(u"Request Account Activation")

	def validate(self):
		if not Form.validate(self):
			return False
		self.site_url.data = self.site_url.data.rstrip("/")

class SetupEmailForm(Form):
	smtp_server = fields.TextField(u"SMTP Server", validators=[validators.Required()])
	smtp_username = fields.TextField(u"Username")
	smtp_password = fields.TextField(u"Password")
	smtp_use_ssl = fields.BooleanField(u"Use SSL")
	smtp_from_addr = fields.TextField(u"Default Sender", validators=[validators.Required()])

class SetupLDAPForm(Form):
	ldap_enabled = fields.BooleanField(u"Enable LDAP")
	ldap_url = fields.TextField(u"URL")
	ldap_basedn = fields.TextField(u"Base DN")

class SetupGitHubForm(Form):
	github_enabled = fields.BooleanField(u"Enable GitHub")
	github_client_id = fields.TextField(u"Client ID")
	github_client_secret = fields.TextField(u"Client Secret")
	github_scope = fields.TextField(u"Scope")

class SetupBitBucketForm(Form):
	bitbucket_enabled = fields.BooleanField(u"Enable BitBucket")
	bitbucket_key = fields.TextField(u"Key")
	bitbucket_secret = fields.TextField(u"Secret")

class SetupMailChimpForm(Form):
	mailchimp_enabled = fields.BooleanField(u"Enable MailChimp")
	mailchimp_api_key = fields.TextField(u"API Key")
	mailchimp_list_news = fields.TextField(u"News List ID")

