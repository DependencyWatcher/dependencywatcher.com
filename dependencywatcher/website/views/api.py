#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from flask import Response, request
from dependencywatcher.website.webapp import app, db
from dependencywatcher.website.model import Repository
from dependencywatcher.repo import Repo
from dependencywatcher.website.plans import PlanException
from flask.ext.login import current_user, login_required
from urllib import unquote
from werkzeug import secure_filename
import os, errno

@app.route("/api/v1/repository/<path:name>", methods=["PUT"])
@login_required
def update_repository(name):
	name = unquote(name)
	existing_repo = current_user.get_repository(name)

	uploaded_file = request.files["file"]
	tmp_file = os.path.join(current_user.get_workdir(), ".uploads", secure_filename(uploaded_file.filename))
	try:
		os.makedirs(os.path.dirname(tmp_file))
	except OSError, e:
		if e.errno == errno.EEXIST:
			pass
		else:
			raise
	uploaded_file.save(tmp_file)

	if existing_repo:
		repo = existing_repo
	else:
		repo = Repository()
		repo.type = Repository.FILE
		repo.private = True
		repo.url = name

	try:
		Repo.create(user=current_user, repo=repo, file_path=tmp_file).fetch_or_update()
	finally:
		os.remove(tmp_file)

	if not existing_repo:
		try:
			current_user.add_repository(repo)
			current_user.purge_repositories()
			db.session.commit()
		except PlanException:
			return Response(u"You have reached your limit of repositories number", 402)

	from dependencywatcher.tasks import fetch_repository
	fetch_repository.delay(current_user.email, repo.url)
	return Response(status=201)

