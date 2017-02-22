#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from flask import render_template, request, redirect, url_for
from dependencywatcher.website.webapp import app
from dependencywatcher.website.model import *
from dependencywatcher.version import Version
from flask.ext.login import login_required, current_user

@app.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
	return redirect(url_for("dashboard_overview"))

@app.route("/dashboard/overview", methods=["GET"])
@login_required
def dashboard_overview():
	if current_user.repositories.count() == 0:
		return redirect(url_for("repository_import"))
	return render_template("overview.html", stats=current_user.stats)

@app.route("/dashboard/repositories", methods=["GET"])
@login_required
def dashboard_repositories():
	cursor = current_user.repositories.filter_by(deleted=False)
	q = request.args.get("q", "")
	if len(q):
		cursor = cursor.filter(Repository.url.contains(q))
	return render_template("repositories.html", repos=cursor.all())

@app.route("/dashboard/alerts", methods=["GET"])
@app.route("/dashboard/alerts/<int:page>", methods=["GET"])
@login_required
def dashboard_alerts(page=1):
	show_fixed = request.args.get("fixed", "false") != "false"

	cursor = Alert.query.join(Alert.reference).join(DependencyReference.repository) \
		.filter(Repository.user_id == current_user.id, Repository.deleted == False) \
			.filter(Alert.fixed == show_fixed)

	q = request.args.get("q", "")
	if len(q) > 0:
		cursor = cursor.join(DependencyReference.dependency).filter(Dependency.name.contains(q) | Repository.url.contains(q))
	if request.args.get("unread", "true") == "true":
		cursor = cursor.filter(Alert.read == False)

	type = request.args.get("type", "")
	filter_types = []
	if type == "versions":
		filter_types.append(Alert.NEW_VERSION)
	if type == "licenses":
		filter_types.extend([Alert.NEW_LICENSE, Alert.BAD_LICENSE])
	if len(filter_types) > 0:
		cursor = cursor.filter(Alert.type.in_(filter_types))

	return render_template("alerts.html", alerts=cursor.order_by(Alert.created.desc()).paginate(page=page, per_page=5), Version=Version)

