#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from flask import render_template, request, redirect, url_for
from dependencywatcher.website.webapp import app
from dependencywatcher.website.plans import Plan
from flask.ext.login import current_user, login_required

@app.route("/upgrade", methods=["GET", "POST"])
@login_required
def upgrade_plan():
	info = None
	if request.method == "POST":
		info = u"Temporarily, in order to proceed please contact <a href=\"mailto:sales@dependencywatcher.com\" class=\"restore-btn alert-link\">sales@dependencywatcher.com</a>" 
	chosen_plan = Plan.by_type(int(request.args.get("plan", Plan.COMPANY)))
	return render_template("upgrade.html", plan=chosen_plan, info=info, Plan=Plan)

