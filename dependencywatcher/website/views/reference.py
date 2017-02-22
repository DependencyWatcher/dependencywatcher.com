#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from flask import render_template, request, Response, abort, url_for
from dependencywatcher.website.webapp import app
from dependencywatcher.website.model import *
from dependencywatcher.repo import Repo
from flask.ext.login import current_user, login_required
import os

@app.route("/reference/<id>", methods=["GET"])
@login_required
def reference_view(id):
	reference = DependencyReference.query.join(DependencyReference.repository). \
		filter(DependencyReference.id == id, Repository.user_id == current_user.id).first_or_404()

	file = os.path.join(Repo(repo=reference.repository, user=current_user).repo_path, reference.file)
	content = None
	warning = None
	try:
		if os.path.getsize(file) < 50000:
			with open(file, "r") as f:
				content = f.read()
		else:
			warning = "File size is too large: %s" % reference.file 
	except OSError:
		warning = "File not found: %s" % reference.file 

	return render_template("reference.html", \
		title = "%s" % os.path.basename(file), \
		file = reference.file, \
		line = reference.line, \
		content = content, \
		warning = warning)

