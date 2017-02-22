#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from flask import render_template, request, abort, Response, redirect, url_for, send_from_directory
from dependencywatcher.db_conf import DBConf
from dependencywatcher.website.webapp import app
from dependencywatcher.website.model import *
from dependencywatcher.website.forms import *
from dependencywatcher.website.plans import Plan
from flask.ext.login import current_user, login_required

@app.errorhandler(403)
def not_authorized(e):
	return render_template("errors/403.html"), 403

@app.errorhandler(404)
def page_not_found(e):
	return render_template("errors/404.html"), 404

@app.route("/robots.txt")
@app.route("/sitemap.xml")
def static_from_root():
	return send_from_directory(app.static_folder, request.path[1:])

@app.route("/", methods=["GET"])
def index():
	config = DBConf.get()
	if current_user.is_authenticated:
		if config.on_premise and config.smtp_server is None and current_user.has_roles("admin"):
			return redirect(url_for("setup_email"))
		if current_user.repositories.filter_by(deleted=False).count() == 0:
			return redirect(url_for("repository_import"))
		return redirect(url_for("dashboard"))
	if config.on_premise:
		return redirect("login")
	return render_template("index.html")

@app.route("/about", methods=["GET"])
def about():
	return render_template("about.html")

@app.route("/pricing", methods=["GET"])
def pricing():
	return render_template("pricing.html", Plan=Plan)

@app.route("/terms", methods=["GET"])
def terms():
	return render_template("terms.html")

@app.route("/privacy", methods=["GET"])
def privacy():
	return render_template("privacy.html")

@app.route("/help/integration", methods=["GET"])
@login_required
def help_integration():
	return render_template("help_integration.html")

@app.route("/help/integration/maven", methods=["GET"])
@login_required
def help_integration_maven():
	return render_template("help_integration_maven.html")

@app.route("/help/integration/shell", methods=["GET"])
@login_required
def help_integration_shell():
	return render_template("help_integration_shell.html")

