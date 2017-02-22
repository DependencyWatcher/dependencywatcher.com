#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from flask import render_template, request, jsonify
from dependencywatcher.website.webapp import app
from flask.ext.login import current_user, login_required
from celery.result import AsyncResult

@app.route("/task/<ids>", methods=["GET"])
@login_required
def get_task(ids):
	from dependencywatcher.tasks import celery
	data = []
	for id in ids.split(","):
		r = celery.AsyncResult(id)
		result = r.result
		if r.state == "FAILURE":
			try:
				result = r.result["exc_message"]
			except:
				result = str(r.result)
				pass
		data.append({
			"id": id,
			"state": r.state,
			"result": result
		})
	return jsonify(data=data)

