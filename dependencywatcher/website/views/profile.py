#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from flask import render_template, request, redirect, url_for
from dependencywatcher.website.webapp import app, db
from dependencywatcher.website.forms import *
from dependencywatcher.website.model import *
from dependencywatcher.website.plans import *
from flask.ext.login import current_user, login_required

@app.route("/profile", methods=["GET"])
@login_required
def profile():
	return redirect(url_for("profile_account"))

@app.route("/profile/account", methods=["GET", "POST"])
@login_required
def profile_account():
	form = ProfileAccountForm(request.form)
	if form.validate_on_submit():
		image_file = request.files[form.image.name]
		image_stream = image_file.stream if image_file.filename else None
		password = form.password.data if form.password else None
		current_user.update(form.name.data, form.email.data, password, image_stream)
		db.session.commit()
		return render_template("profile_account.html", form=form, success=u"Your account has been updated successfully")
	return render_template("profile_account.html", form=form)

@app.route("/profile/alerts", methods=["GET", "POST"])
@login_required
def profile_alerts():
	form = UserSettingsForm(request.form)
	if form.validate_on_submit():
		form.populate_obj(current_user.settings)
		db.session.commit()
		return render_template("profile_alerts.html", form=form, success=u"Alerts settings have been updated successfully")
	return render_template("profile_alerts.html", form=form)

@app.route("/profile/plan", methods=["GET"])
@login_required
def profile_plan():
	return render_template("profile_plan.html", plan=current_user.get_plan(), Plan=Plan)

@app.route("/profile/keys", methods=["GET", "POST"])
@login_required
def profile_keys():
	if request.method == "POST":
		current_user.generate_key_pair(force=True)
		db.session.commit()
	return render_template("profile_keys.html")

@app.route("/profile/apikey", methods=["GET", "POST"])
@login_required
def profile_api_key():
	if request.method == "POST":
		current_user.generate_api_key(force=True)
		db.session.commit()
	return render_template("profile_api_key.html")
