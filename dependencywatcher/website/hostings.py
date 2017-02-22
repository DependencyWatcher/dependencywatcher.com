#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

import requests, re, logging, json
from flask_oauth import OAuth
from dependencywatcher.db_conf import DBConf

class GitHostingAPI(object):
    DEPLOY_KEY_LABEL = "DependencyWatcher-integration-key"
    REPO_GIT_URL_RE = re.compile("git@(.*):(.*?)/(.*)")
    REPO_MERCURIAL_URL_RE = re.compile("ssh://hg@(.*)/(.*)/(.*)")

    def __init__(self):
        self.cache = {}

    def _get(self, endpoint):
        raise NotImplementedError

    def _get_cached(self, endpoint):
        if not endpoint in self.cache:
            self.cache[endpoint] = self._get(endpoint)
        return self.cache[endpoint]

    def _post(self, endpoint, params):
        raise NotImplementedError

    def _delete(self, endpoint):
        raise NotImplementedError

    def _get_deploy_key_api_info(self, repo_url):
        raise NotImplementedError

    @staticmethod
    def extract_repo_info(repo_url):
        match = GitHostingAPI.REPO_MERCURIAL_URL_RE.match(repo_url)
        if not match:
            match = GitHostingAPI.REPO_GIT_URL_RE.match(repo_url)
            if not match:
                raise Exception("Can't extract service info from repository URL: %s" % repo_url)
        (service, owner, slug) = (match.group(1), match.group(2), match.group(3))
        if service == "bitbucket.org" and slug.endswith(".git"):
            slug = slug[:-4]
        return (service, owner, slug)

    def put_deploy_key(self, user, repo_url, force=False):
        user.generate_key_pair(force)

        (service, owner, slug) = GitHostingAPI.extract_repo_info(repo_url)
        (base_url, title_field, id_field) = self._get_deploy_key_api_info(owner, slug)

        # Check existing deploy key:
        for k in self._get(base_url):
            if k[title_field] == GitHostingAPI.DEPLOY_KEY_LABEL:
                if k["key"] != user.keypair.public:
                    self._delete("%s/%s" % (base_url, k[id_field]))
                    break
                return

        # Add new key:
        self._post(base_url, {"key": user.keypair.public, title_field: GitHostingAPI.DEPLOY_KEY_LABEL})

    @staticmethod
    def create_for_repo(user, repo_url):
        try:
            (service, owner, slug) = GitHubAPI.extract_repo_info(repo_url)
            if "github.com" == service:
                return GitHubAPI(user=user)
            if "bitbucket.org" == service:
                return BitBucketAPI(user=user)
        except:
            pass
        return None


class BitBucketAPI(GitHostingAPI):
    def __init__(self, oauth_data=None, user=None):
        super(BitBucketAPI, self).__init__()

        conf = DBConf.get()
        self.remote = OAuth().remote_app("bitbucket",
            base_url="https://bitbucket.org/!api/1.0/",
            request_token_url="https://bitbucket.org/!api/1.0/oauth/request_token",
            access_token_url="https://bitbucket.org/!api/1.0/oauth/access_token",
            authorize_url="https://bitbucket.org/!api/1.0/oauth/authenticate",
            consumer_key=conf.bitbucket_key,
            consumer_secret=conf.bitbucket_secret
        )

        if oauth_data is None:
            if not user is None and user.is_authenticated and user.bitbucket is not None:
                oauth_data = json.loads(user.bitbucket)
        self.token = None
        if oauth_data is not None:
            try:
                self.token = (oauth_data["oauth_token"], oauth_data["oauth_token_secret"])
            except KeyError:
                pass

        self.remote.tokengetter_func = self._tokengetter

    def _get_deploy_key_api_info(self, owner, repo_slug):
        return ("repositories/%s/%s/deploy-keys" % (owner, repo_slug), "label", "pk")

    def _tokengetter(self, token=None):
        return self.token

    def get_oauth_data_from_request(self, request):
        if "oauth_verifier" in request.args:
            data = self.remote.handle_oauth1_response()
        elif "code" in request.args:
            data = self.remote.handle_oauth2_response()
        else:
            data = self.remote.handle_unknown_response()
        self.remote.free_request_token()
        return data

    def web_authorize(self, callback):
        """ This is a wrapper to OAuth's authorize method """
        return self.remote.authorize(callback=callback)

    def _get(self, endpoint):
        if not endpoint in self.cache:
            self.cache[endpoint] = self.remote.get(endpoint, token="detect").data
        return self.cache[endpoint]

    def _post(self, endpoint, params):
        self.remote.post(endpoint, data=params, token="detect")

    def _delete(self, endpoint):
        self.remote.delete(endpoint, token="detect")

    def get_user(self):
        return self._get_cached("user")["user"]

    def get_username(self):
        return self.get_user()["username"]

    def get_user_emails(self):
        return self._get_cached("users/%s/emails" % self.get_username())

    def get_user_repos(self):
        return self._get_cached("user/repositories")


class GitHubAPI(GitHostingAPI):
    """ Facade for the GitHub API """
    BASE_URI = "https://api.github.com"

    def __init__(self, oauth_data=None, user=None):
        super(GitHubAPI, self).__init__()

        if oauth_data is None:
            if user is None or not user.is_authenticated and user.github is not None:
                raise NoTokenException()
            oauth_data = json.loads(user.github)
        try:
            self.headers = { "Authorization": "token %s" % oauth_data["access_token"] }
        except KeyError:
            raise NoTokenException()

    def _get(self, url):
        endpoint = GitHubAPI.BASE_URI + url
        if not endpoint in self.cache:
            self.cache[endpoint] = requests.get(endpoint, headers=self.headers).json()
        return self.cache[endpoint]

    def _post(self, endpoint, params):
        requests.post(endpoint, headers=self.headers, data=params)

    def _delete(self, endpoint):
        requests.delete(endpoint, headers=self.headers)

    def get_user(self):
        return self._get_cached("/user")

    def get_user_repos(self):
        return self._get_cached("/user/repos")

    def get_user_orgs(self):
        return self._get_cached("/user/orgs")

    def get_org_repos(self, org):
        return self._get_cached("/orgs/%s/repos" % org)

    def get_all_user_repos(self):
        all = []
        all.extend(self.get_user_repos())
        for org in self.get_user_orgs():
            all.extend(self.get_org_repos(org["login"]))
        return all

class NoTokenException(Exception):
    pass

