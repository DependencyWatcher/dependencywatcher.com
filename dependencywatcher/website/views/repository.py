#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from flask import render_template, request, Response, abort, url_for, make_response, redirect
from dependencywatcher.version import Version
from dependencywatcher.website.webapp import app, db
from dependencywatcher.website.forms import *
from dependencywatcher.website.plans import *
from dependencywatcher.website.model import *
from dependencywatcher.repo import Repo
from flask.ext.login import current_user, login_required
from urllib import unquote
from werkzeug import secure_filename
import urllib, os, errno, datetime

def import_repositories(repositories):
    from dependencywatcher.tasks import fetch_repository
    try:
        for repo in repositories:
            current_user.add_repository(repo)

        current_user.purge_repositories()
        db.session.commit()

        tasks = []
        for repo in repositories:
            result = fetch_repository.delay(current_user.email, repo.url)
            tasks.append({"id": result.id, "title": "Importing %s" % repo.url})

        return render_template("repository_import_p.html", tasks=tasks)

    except PlanException:
        return render_template("msgbox.html", msgtitle=u"Import Repository",
            msgtext=u"""You have reached your limit of repositories number.
                To view your current plan usage please visit <a href='%s'>plan details</a> page.""" % url_for("profile_plan"))

def update_repositories(repositories):
    from dependencywatcher.tasks import fetch_repository
    tasks = []
    for repo in repositories:
        result = fetch_repository.delay(current_user.email, repo.url)
        tasks.append({"id": result.id, "title": "Updating %s" % repo.url})

    return render_template("repository_import_p.html", tasks=tasks)

@app.route("/repository/import", methods=["GET", "POST"])
@login_required
def repository_import():
    form = RepositoryImportForm(request.form)
    if form.validate_on_submit():
        repo = Repository(user_id=current_user.id)
        form.populate_obj(repo) 
        repo.private = repo.auth_type != repo.AUTH_NONE
        if current_user.has_repository(repo.url):
            return render_template("repository_import.html", form=form, error=u"This repository has been imported already!", Repository=Repository)
        else:
            return import_repositories([repo])
    return render_template("repository_import.html", form=form, Repository=Repository)

@app.route("/repositories/import", methods=["POST"])
@login_required
def repositories_import():
    repositories = []
    for repo_url, private, type in zip(request.form.getlist("repo_url[]"), request.form.getlist("private[]"), request.form.getlist("type[]")):
        repo = Repository()
        repo.type = type
        repo.url = repo_url
        repo.private = private == "True"
        repositories.append(repo)
    return import_repositories(repositories)

@app.route("/repository/<path:url>", methods=["GET"])
@app.route("/repository/<path:url>/<int:page>", methods=["GET"])
@login_required
def repository_view(url, page=1):
    url = unquote(url)
    repo = current_user.get_repository(url)
    if not repo is None:
        repo.mark_viewed()

        cursor = repo.references
        q = request.args.get("q", "")
        if len(q) > 0:
            cursor = cursor.join(DependencyReference.dependency).filter(Dependency.name.contains(q))
        if request.args.get("old_v", "false") == "true":
            cursor = cursor.join(DependencyReference.alerts).filter(Alert.type == Alert.NEW_VERSION)

        return render_template("repository.html", repo=repo, deps=cursor.paginate(page=page, per_page=7))
    abort(404)

@app.route("/shield/<path:url>", methods=["GET"])
@login_required
def repository_shield(url):
    url = unquote(url)
    repo = current_user.get_repository(url)
    if not repo is None:
        repo_stats = repo.stats
        outdated_percent = int(repo_stats.outdated * 100 / repo_stats.deps) if repo_stats.deps > 0 else 0
        response = make_response(render_template("svg/shield.svg", percent=outdated_percent))
        response.headers["Content-Type"] = "image/svg+xml"
        return response
    abort(404)

@app.route("/repository/<path:url>", methods=["DELETE"])
@login_required
def repository_delete(url):
    url = unquote(url)
    if current_user.delete_repository(url):
        db.session.commit()
        return Response(status=202)
    abort(404)

@app.route("/repository/<path:url>/restore", methods=["PUT"])
@login_required
def repository_restore(url):
    url = unquote(url)
    if current_user.restore_repository(url):
        db.session.commit()
        return Response(status=202)
    abort(404)

@app.route("/repository/<path:url>/upload", methods=["GET", "POST"])
@app.route("/repository/upload", methods=["GET", "POST"])
@login_required
def repository_upload(url=None):
    existing_repo = None
    if url:
        url = unquote(url)
        existing_repo = current_user.get_repository(url)
        if not existing_repo:
            abort(404)

    form = RepositoryUploadForm(request.form)
    if form.validate_on_submit():

        uploaded_file = request.files[form.file.name]
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
            repo.url = form.name.data

        try:
            Repo.create(user=current_user, repo=repo, file_path=tmp_file).fetch_or_update()
        except Exception as e:
            return render_template("repository_upload.html", form=form, error=str(e), repo=existing_repo)
        finally:
            os.remove(tmp_file)

        return update_repositories([repo]) if existing_repo else import_repositories([repo])

    return render_template("repository_upload.html", form=form, repo=existing_repo)

@app.route("/repository/<repo_name>/upload.sh", methods=["GET"])
@login_required
def repository_upload_script(repo_name):
    if current_user.api_key is None:
        return redirect(url_for("profile_api_key"))
    response = make_response(render_template("scripts/upload.sh", repo_name=repo_name))
    response.headers["Content-Type"] = "application/x-shellscript"
    return response

