#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

import os, errno

from dependencywatcher.repo import Repo
from dependencywatcher.website.model import Repository
from dependencywatcher.crawler.manifest import FileManifestLoader

class Manifests(object):
    """ Interface for getting updates to manifests from GitHub repository """

    def __init__(self, workdir):
        manifest_repo = Repository()
        manifest_repo.url = "https://github.com/DependencyWatcher/manifests.git"
        manifest_repo.type = Repository.GIT
        self.repo = Repo.create(workdir=workdir, repo=manifest_repo)
        self.workdir = os.path.join(workdir, "manifests.git")

    def load(self, name):
        try:
            return FileManifestLoader(parent_dir=self.workdir).load(name)
        except IOError, e:
            if e.errno == errno.ENOENT:
                return None
            else:
                raise

    def sync(self):
        self.repo.fetch_or_update()

