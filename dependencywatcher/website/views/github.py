#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from flask import render_template, request, abort, redirect, url_for, session
from dependencywatcher.website.hostings import GitHubAPI, NoTokenException
from dependencywatcher.db_conf import DBConf
from dependencywatcher.website.webapp import app
from dependencywatcher.website.model import Repository, User
from dependencywatcher.website.login import OAuthLogin
from flask.ext.login import current_user, login_required
import string, random, requests, json, urllib

class GitHubLogin(OAuthLogin):
    def __init__(self, oauth_data):
        super(GitHubLogin, self).__init__("github", oauth_data)

    def _get_user_data(self):
        try:
            return self.user_data
        except AttributeError:
            self.user_data = GitHubAPI(self.oauth_data, current_user).get_user()
        return self.user_data

    def find_existing_user(self):
        return User.query.filter_by(email=self.get_remote_email()).first()

    def get_remote_email(self):
        return self._get_user_data()["email"]

    def get_remote_display_name(self):
        return self._get_user_data()["name"]

    def get_remote_avatar(self):
        try:
            return self._get_user_data()["avatar_url"]
        except KeyError:
            return None

@app.route("/github/authorize", methods=["GET"])
def github_authorize():
    conf = DBConf.get()
    session["github_state"] = "".join(random.choice(string.hexdigits) for _ in range(32))
    params = {"client_id": conf.github_client_id, "scope": conf.github_scope, "state": session["github_state"]}
    try:
        session["github_next_url"] = request.args["next"]
    except KeyError:
        pass
    return redirect("https://github.com/login/oauth/authorize?%s" % urllib.urlencode(params))

@app.route("/github/callback", methods=["GET"])
def github_callback():
    try:
        if session["github_state"] == request.args["state"]:
            del session["github_state"]
        else:
            abort(403)
    except KeyError:
        abort(403)

    conf = DBConf.get()
    r = requests.post("https://github.com/login/oauth/access_token", 
        data = json.dumps({
            "client_id": conf.github_client_id, 
            "client_secret": conf.github_client_secret, 
            "code": request.args["code"]
        }),
        headers = {"Content-Type":"application/json", "Accept": "application/json"}
    )
    GitHubLogin(r.json()).handle_callback()

    next = url_for("index")
    try:
        next = session["github_next_url"]
        del session["github_next_url"]
    except KeyError:
        pass
    return redirect(next)

@app.route("/github/import", methods=["GET"])
@login_required
def github_import():
    try:
        github = GitHubAPI(user=current_user)
    except:
        return redirect("%s?%s" % (url_for("github_authorize"), urllib.urlencode({"next": url_for("github_import")})))

    repos = []
    for r in github.get_all_user_repos():
        repo_url = r["ssh_url"] if r["private"] else r["clone_url"]
        if not current_user.has_repository(repo_url):
            repos.append({
                "html_url": r["html_url"],
                "full_name": r["full_name"],
                "description": r["description"],
                "url": repo_url,
                "private": r["private"],
                "type": Repository.GIT
            })
    return render_template("repositories_import.html", repos=repos, service_name="GitHub", icon_class="fa-github")

@app.route("/github/login", methods=["GET"])
def github_login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    return redirect("%s?%s" % (url_for("github_authorize"),
        urllib.urlencode({"next": request.args.get("next") or url_for("index")})))

