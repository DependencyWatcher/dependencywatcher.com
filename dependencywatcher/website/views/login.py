#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from flask import render_template, request, abort, redirect, url_for
from dependencywatcher.db_conf import DBConf
from dependencywatcher.website.webapp import app, db
from dependencywatcher.website.model import *
from dependencywatcher.website.forms import *
from flask.ext.login import login_user, logout_user, current_user, login_required

@app.route("/login", methods=["GET", "POST"])
def login():
	if current_user.is_authenticated:
		return redirect(url_for("index"))
	form = LoginForm(request.form)
	if form.validate_on_submit():
		login_user(form.user)
		form.user.purge_repositories()
		db.session.commit()
		return redirect(request.args.get("next") or url_for("index"))
	return render_template("login.html", form=form)

@app.route("/signup", methods=["GET", "POST"])
def signup():
	if current_user.is_authenticated:
		return redirect(url_for("index"))

	form = SignupForm(request.form)
	if form.validate_on_submit():
		user = User()
		user.init(form.name.data, form.email.data, form.password.data)
		db.session.add(user)

		if DBConf.get().request_activation:
			user.request_activation()
			db.session.commit()
			return render_template("msgbox.html", msgtitle=u"Account registration",
				msgtext=u"""Thank you for registering at DependencyWatcher!
					To complete registration please check your email for additional instructions.""")
		else:
			user.perform_new_user_actions()
			db.session.commit()
			login_user(user)
			return redirect(url_for("index"))

	return render_template("signup.html", form=form)

@app.route("/activate/request/<email>", methods=["GET"])
def request_activation(email):
	if current_user.is_authenticated:
		return redirect(url_for("index"))
	user = User.query.filter_by(email=email).first_or_404()
	if not user.is_active():
		user.request_activation()
		db.session.commit()
	return render_template("msgbox.html", msgtitle=u"Account activation",
		msgtext=u"""Please check your email for additional instructions.""")

@app.route("/activate/<code>", methods=["GET"])
def activate(code):
	user = User.query.filter_by(activation_code=code).first_or_404()
	user.activate_with_code(code)
	user.perform_new_user_actions()
	db.session.commit()
	login_user(user)
	return render_template("msgbox.html", msgtitle=u"Account activation",
		msgtext=u"You account has been activated successfully! To proceed click <a href='/' class='alert-link'>here</a>.")

@app.route("/password/recovery", methods=["GET", "POST"])
def password_recovery():
	if current_user.is_authenticated:
		return redirect(url_for("index"))
	if request.method == "POST":
		user = User.query.filter_by(email=request.form["email"]).first()
		if not user is None:
			user.request_recovery()
			db.session.commit()
		return render_template("msgbox.html", msgtitle=u"Password recovery",
			msgtext=u"Password recovery instructions have been sent to <a href='mailto:%s' class='alert-link'>%s</a>" % (user.email, user.email))
	return render_template("password_recovery.html")

@app.route("/password/recovery/<code>", methods=["GET"])
def password_recovery_start(code):
	user = User.query.filter_by(recovery_code=code).first_or_404()
	login_user(user)
	return redirect(url_for("password_reset"))

@app.route("/password/reset", methods=["GET", "POST"])
@login_required
def password_reset():
	form = PasswordResetForm(request.form)
	if form.validate_on_submit():
		current_user.password_reset(form.password.data)
		db.session.commit()
		return render_template("msgbox.html", msgtitle=u"New Password",
			msgtext=u"New password has been set successfully! To proceed click <a href='/' class='alert-link'>here</a>.")
	return render_template("password_reset.html", form=form)

@app.route("/logout", methods=["GET"])
def logout():
	logout_user()
	return redirect(request.args.get("next") or url_for("index"))

