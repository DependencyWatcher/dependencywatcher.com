#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from flask import render_template, request, abort, redirect, url_for, session, Response
from dependencywatcher.website.webapp import app
from dependencywatcher.website.hostings import BitBucketAPI, NoTokenException
from dependencywatcher.website.login import OAuthLogin
from dependencywatcher.website.model import Repository, User
from flask.ext.login import current_user, login_required, login_user
import string, random, requests, json, urllib
from flask_oauth import OAuthException

class BitBucketLogin(OAuthLogin):
    def __init__(self, oauth_data):
        super(BitBucketLogin, self).__init__("bitbucket", oauth_data)
        self.bitbucket = BitBucketAPI(oauth_data, current_user)

    def find_existing_user(self):
        return User.query.filter(User.email.in_([e["email"] for e in self.bitbucket.get_user_emails()])).first()

    def get_remote_email(self):
        return next(e["email"] for e in self.bitbucket.get_user_emails() if e["primary"])

    def get_remote_display_name(self):
        return self.bitbucket.get_user()["display_name"]

    def get_remote_avatar(self):
        try:
            return self.bitbucket.get_user()["avatar"].replace("s=32", "s=128")
        except KeyError:
            return None

@app.route("/bitbucket/authorize", methods=["GET"])
def bitbucket_authorize():
    return BitBucketAPI(user=current_user).web_authorize(callback=url_for("bitbucket_callback",
        next=request.args.get("next") or request.referrer or None, _external=True))

@app.route("/bitbucket/callback", methods=["GET"])
def bitbucket_callback():
    bitbucket_data = BitBucketAPI(user=current_user).get_oauth_data_from_request(request)
    if bitbucket_data is None:
        abort(403)

    BitBucketLogin(bitbucket_data).handle_callback()
    return redirect(request.args.get("next", url_for("index")))

@app.route("/bitbucket/import", methods=["GET"])
@login_required
def bitbucket_import():
    try:
        repositories = BitBucketAPI(user=current_user).get_user_repos()
    except OAuthException as e:
        if e.type == "token_missing":
            return redirect("%s?%s" % (url_for("bitbucket_authorize"), urllib.urlencode({"next": url_for("bitbucket_import")})))
        raise e
    repos = []
    for r in repositories:
        type = Repository.MERCURIAL if r["scm"] == "hg" else Repository.GIT
        if type == Repository.GIT:
            repo_url = "git@bitbucket.org:%s/%s.git" % (r["owner"], r["slug"])
        else:
            repo_url = "ssh://hg@bitbucket.org/%s/%s" % (r["owner"], r["slug"])
        if not current_user.has_repository(repo_url):
            repos.append({
                "html_url": "https://bitbucket.org/%s/%s" % (r["owner"], r["slug"]),
                "full_name": r["name"],
                "description": r["description"],
                "url": repo_url,
                "private": r["is_private"],
                "type": type
            })
    return render_template("repositories_import.html", repos=repos, service_name="BitBucket", icon_class="fa-bitbucket")

@app.route("/bitbucket/login", methods=["GET"])
def bitbucket_login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    return redirect("%s?%s" % (url_for("bitbucket_authorize"),
        urllib.urlencode({"next": request.args.get("next") or url_for("index")})))

