#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from flask import jsonify, Response, render_template
from dependencywatcher.website.webapp import app, db
from dependencywatcher.website.model import Alert, DependencyReference, Repository
from flask.ext.login import current_user, login_required

@app.route("/alert/<id>/read", methods=["PUT"])
@login_required
def mark_as_read(id):
	alert = Alert.query.join(Alert.reference).join(DependencyReference.repository) \
		.filter(Repository.user_id == current_user.id, Alert.id == id).first_or_404()
	alert.read = True
	db.session.commit()
	return Response(status=202)

@app.route("/alert/<id>/unread", methods=["PUT"])
@login_required
def mark_as_unread(id):
	alert = Alert.query.join(Alert.reference).join(DependencyReference.repository) \
		.filter(Repository.user_id == current_user.id, Alert.id == id).first_or_404()
	alert.read = False
	db.session.commit()
	return Response(status=202)

