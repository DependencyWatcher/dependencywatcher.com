#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from flask import render_template, request, redirect, url_for
from dependencywatcher.db_conf import DBConf
from dependencywatcher.website.webapp import app, db
from dependencywatcher.website.forms import *
from dependencywatcher.website.model import *
from dependencywatcher.website.login import requires_roles
from flask.ext.login import current_user, login_required

def process_request(template, form):
	if form.validate_on_submit():
		config = Config.query.one()
		form.populate_obj(config)
		db.session.commit()
		DBConf.reload()
		return render_template(template, form=form, success=u"Configuration has been updated successfully")
	return render_template(template, form=form)

@app.route("/setup", methods=["GET"])
@login_required
@requires_roles("admin")
def setup():
	return redirect(url_for("setup_website"))

@app.route("/setup/website", methods=["GET", "POST"])
@login_required
@requires_roles("admin")
def setup_website():
	return process_request("setup_website.html", SetupWebsiteForm(request.form))

@app.route("/setup/email", methods=["GET", "POST"])
@login_required
@requires_roles("admin")
def setup_email():
	return process_request("setup_email.html", SetupEmailForm(request.form))

@app.route("/setup/ldap", methods=["GET", "POST"])
@login_required
@requires_roles("admin")
def setup_ldap():
	return process_request("setup_ldap.html", SetupLDAPForm(request.form))

@app.route("/setup/github", methods=["GET", "POST"])
@login_required
@requires_roles("admin")
def setup_github():
	return process_request("setup_github.html", SetupGitHubForm(request.form))

@app.route("/setup/bitbucket", methods=["GET", "POST"])
@login_required
@requires_roles("admin")
def setup_bitbucket():
	return process_request("setup_bitbucket.html", SetupBitBucketForm(request.form))

@app.route("/setup/mailchimp", methods=["GET", "POST"])
@login_required
@requires_roles("admin")
def setup_mailchimp():
	return process_request("setup_mailchimp.html", SetupMailChimpForm(request.form))

