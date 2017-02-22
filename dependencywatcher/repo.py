#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

import os, subprocess, re, sys, hashlib, pipes, errno, shutil, datetime, patoolib, traceback

class Diff(object):
    def __init__(self):
        self.added = []
        self.updated = []
        self.deleted = []

class Repo(object):
    RE_DIFF = re.compile("([A-Z])\s+(.*)")

    """ Git or SSH repository object """
    def __init__(self, repo, user=None, workdir=None):
        if workdir is None:
            workdir = user.get_workdir()
        self.workdir = workdir
        self.user = user
        if not os.path.exists(self.workdir):
            try:
                os.makedirs(self.workdir)
            except OSError, e:
                if e.errno == errno.EEXIST:
                    pass
                else:
                    raise
        self.repo = repo
        self.repo_path = os.path.join(workdir, os.path.basename(repo.url))

        if repo.ssh_key is not None:
            self._create_keyfile(repo.ssh_key)
        elif self.repo.private:
            try:
                self._upload_deploy_key()
            except:
                traceback.print_exc()
                raise Exception(u"Can't import remote Git repository. Please make sure that you have sufficient permissions to update deploy keys!")
        else:
            self._create_ssh_wrapper()

    def _read_lines(self, stream):
        line = ""
        while True:
            ch = stream.read(1)
            if not ch:
                break
            if ch in ["\r", "\n"]:
                yield line
                line = ""
            else:
                line += ch

    def _create_keyfile(self, ssh_key):
        md5 = hashlib.md5()
        md5.update(ssh_key)
        self.ssh_keyfile = os.path.join(self.workdir, ".%s.key" % md5.hexdigest())
        if not os.path.exists(self.ssh_keyfile):
            with open(self.ssh_keyfile, "w") as f:
                f.write(ssh_key)
            os.chmod(self.ssh_keyfile, 0600)
        self._create_ssh_wrapper(self.ssh_keyfile)

    def _create_ssh_wrapper(self, ssh_keyfile=None):
        self.ssh_wrapper = self.ssh_keyfile.replace(".key", ".sh") if ssh_keyfile else os.path.join(self.workdir, "ssh-wrapper")
        if not os.path.exists(self.ssh_wrapper):
            content = "#!/bin/sh\nexec ssh -oStrictHostKeyChecking=no -oUserKnownHostsFile=/dev/null -oBatchMode=yes"
            if ssh_keyfile:
                content += " -i %s" % pipes.quote(ssh_keyfile)
            content +=  " \"$@\""
            with open(self.ssh_wrapper, "w") as f:
                f.write(content)
            os.chmod(self.ssh_wrapper, 0755)

    def _upload_deploy_key(self, force=False):
        from dependencywatcher.website.hostings import GitHostingAPI
        api = GitHostingAPI.create_for_repo(self.user, self.repo.url)
        if api is not None:
            api.put_deploy_key(self.user, self.repo.url, force)
            self._create_keyfile(self.user.keypair.private)

            # Update repository's SSH key to the deploy key, so the next time we use it directly:
            self.repo.update_ssh_key(self.user.keypair.private)

    def exists(self):
        return os.path.exists(self.repo_path)

    def fetch(self, progress_callback=None):
        """ Fetches remote repository to the working directory """
        raise NotImplementedError

    def update(self, progress_callback=None):
        """ Updates fetched repository """
        raise NotImplementedError

    def fetch_or_update(self, progress_callback=None):
        """ Fetches repository if doesn't exist, otherwise updates it """
        retry_count = 2
        while retry_count > 0:
            try:
                if self.exists():
                    self.update(progress_callback)
                else:
                    self.fetch(progress_callback)
                break
            except DeploymentKeyProblem:
                self._upload_deploy_key(True)
                retry_count = retry_count - 1
        if retry_count == 0:
            raise Exception("Can't update repository %s due to a problem in deployment key" % self.repo_url)

    def diff(self, progress_callback=None):
        """ Finds diff between local repository and remote one """
        diff = Diff()
        self._diff(diff, progress_callback)
        return diff

    def _diff(self, diff, progress_callback=None):
        raise NotImplementedError

    def _add_to_diff(self, diff, line, add_character, delete_character, update_character):
        match = Repo.RE_DIFF.search(line)
        if match:
            flag = match.group(1)
            path = match.group(2)
            if flag == add_character:
                diff.added.append(path)
            elif flag == update_character:
                diff.updated.append(path)
            elif flag == delete_character:
                diff.deleted.append(path)

    def remove(self):
        """ Deletes the reposotory from the disk """
        try:
            shutil.rmtree(self.repo_path)
        except OSError as e:
            if e.errno != 2:
                raise e

    @staticmethod
    def create(repo, user=None, workdir=None, file_path=None):
        """ Create class instance according to the repository type """
        if repo.type == repo.GIT:
            return GitRepo(repo, user, workdir)
        if repo.type == repo.SVN:
            return SVNRepo(repo, user, workdir)
        if repo.type == repo.FILE:
            return FileRepo(repo, user, workdir, file_path)
        if repo.type == repo.MERCURIAL:
            return MercurialRepo(repo, user, workdir)
        raise NotImplementedError(u"Repository utilities not implemented for type: %s" % repo.type)

class GitRepo(Repo):
    RE_PROGRESS = re.compile("Receiving objects:\s+(\d+)%")
    RE_DEPLOYMENT_KEY_PROBLEM = "deployment key is not associated with the requested repository"

    def __init__(self, repo, user=None, workdir=None):
        super(GitRepo, self).__init__(repo, user, workdir)

        self.env = {}
        try:
            self.env["GIT_SSH"] = self.ssh_wrapper
        except AttributeError:
            pass

    def _read_progress(self, stream, progress_callback):
        for line in self._read_lines(stream):
            if GitRepo.RE_DEPLOYMENT_KEY_PROBLEM in line:
                raise DeploymentKeyProblem()
            if progress_callback:
                match = GitRepo.RE_PROGRESS.search(line)
                if match:
                    progress_callback(match.group(1))

    def fetch(self, progress_callback=None):
        if not self.exists():
            proc = subprocess.Popen(["git", "clone", self.repo.url, self.repo_path, "--progress"], env=self.env, stderr=subprocess.PIPE)
            self._read_progress(proc.stderr, progress_callback)
            if proc.wait() != 0:
                raise Exception(u"Can't import remote Git repository. Please make sure the URL is accessible from everywhere!")
        else:
            raise Exception(u"Repository already imported")

    def update(self, progress_callback=None):
        if self.exists():
            proc = subprocess.Popen(["git", "pull", "--progress"], cwd=self.repo_path, env=self.env, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            self._read_progress(proc.stderr, progress_callback)
            output = proc.stdout.read()
            if proc.wait() != 0:
                raise Exception(u"Wrong exit status received from Git command!")

            if not "Already up-to-date" in output:
                self.repo.mark_updated()
        else:
            raise Exception(u"Repository not imported")

    def _diff(self, diff, progress_callback=None):
        if self.exists():
            proc = subprocess.Popen(["git", "fetch", "--progress"], cwd=self.repo_path, env=self.env, stderr=subprocess.PIPE)
            self._read_progress(proc.stderr, progress_callback)
            if proc.wait() != 0:
                raise Exception(u"Wrong exit status received from Git command!")
            
            proc = subprocess.Popen(["git", "diff", "--name-status", "master", "origin/master"], cwd=self.repo_path, env=self.env, stdout=subprocess.PIPE)
            for line in self._read_lines(proc.stdout):
                self._add_to_diff(diff, line, "A", "D", "M")
            if proc.wait() != 0:
                raise Exception(u"Wrong exit status received from Git command!")
        else:
            raise Exception(u"Repository not imported")

class MercurialRepo(Repo):
    RE_MANIFEST_PROGRESS = re.compile("manifests:\s+(\d+)/(\d+)\s+chunks")
    RE_FILES_PROGRESS = re.compile("files:\s+(\d+)/(\d+)\s+chunks")
    RE_UPDATING_PROGRESS = re.compile("updating:\s+.*\s+(\d+)/(\d+)\s+files")

    def __init__(self, repo, user=None, workdir=None):
        super(MercurialRepo, self).__init__(repo, user, workdir)
        self.extra_args = []
        self.env = {}
        try:
            self.extra_args.extend(["--ssh", self.ssh_wrapper])
        except AttributeError:
            pass

    def _read_lines(self, stream):
        line = ""
        while True:
            ch = stream.read(1)
            if not ch:
                break
            if ch in ["\r", "\n"]:
                yield line
                line = ""
            else:
                line += ch

    def _read_progress(self, stream, progress_callback):
        for line in self._read_lines(stream):
            if progress_callback:
                percent = None
                if line == "adding changesets":
                    percent = 10
                else:
                    match = MercurialRepo.RE_MANIFEST_PROGRESS.search(line)
                    if match:
                        percent = 30 + 30 * int(match.group(1)) / int(match.group(2))
                    else:
                        match = MercurialRepo.RE_FILES_PROGRESS.search(line)
                        if match:
                            percent = 60 + 30 * int(match.group(1)) / int(match.group(2))
                        else:
                            match = MercurialRepo.RE_UPDATING_PROGRESS.search(line)
                            if match:
                                percent = 90 + 10 * int(match.group(1)) / int(match.group(2))
                if percent:
                    progress_callback(percent)

    def fetch(self, progress_callback=None):
        if not self.exists():
            proc = subprocess.Popen(["hg", "-v", "--debug", "clone", self.repo.url, self.repo_path] + self.extra_args,
                    env=self.env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self._read_progress(proc.stdout, progress_callback)
            if proc.wait() != 0:
                raise Exception(u"Can't import remote Mercurial repository. Please make sure the URL is accessible from everywhere!")
        else:
            raise Exception(u"Repository already imported")

    def update(self, progress_callback=None):
        if self.exists():
            proc = None
            with open(os.devnull, "w") as devnull:
                proc = subprocess.Popen(["hg", "incoming"] + self.extra_args, cwd=self.repo_path, env=self.env, stdout=devnull, stderr=devnull)
            # Exit status from 'hg incoming' means there are incoming changes:
            if proc.wait() == 0:
                proc = subprocess.Popen(["hg", "-v", "--debug", "pull", "-u"] + self.extra_args,
                        cwd=self.repo_path, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                self._read_progress(proc.stdout, progress_callback)
                if proc.wait() != 0:
                    raise Exception(u"Wrong exit status received from Mercurial command!")
                self.repo.mark_updated()
        else:
            raise Exception(u"Repository not imported")

    def _diff(self, diff, progress_callback=None):
        if self.exists():
            proc = subprocess.Popen(["hg", "-v", "--debug", "pull"] + self.extra_args,
                    cwd=self.repo_path, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self._read_progress(proc.stdout, progress_callback)
            if proc.wait() != 0:
                raise Exception(u"Wrong exit status received from Mercurial command!")
            
            proc = subprocess.Popen(["hg", "summary", "--rev", ".:tip"] + self.extra_args,
                    cwd=self.repo_path, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in self._read_lines(proc.stdout):
                self._add_to_diff(diff, line, "A", "R", "M")
            if proc.wait() != 0:
                raise Exception(u"Wrong exit status received from Mercurial command!")
        else:
            raise Exception(u"Repository not imported")

class SVNRepo(Repo):
    def __init__(self, repo, user=None, workdir=None):
        super(SVNRepo, self).__init__(repo, user, workdir)

        self.extra_args = []
        self.env = {}
        try:
            self.env["SVN_SSH"] = self.ssh_wrapper
        except AttributeError:
            pass
        try:
            self.extra_args.extend(["--username", self.username])
            self.extra_args.extend(["--password", self.password])
        except AttributeError:
            pass

    def _list_repo(self):
        proc = subprocess.Popen(["svn", "list", self.repo.url] + self.extra_args, env=self.env, stdout=subprocess.PIPE)
        stdout, _ = proc.communicate() 
        repo_list = [path.split(os.path.sep)[0] for path in stdout.splitlines()]
        if proc.wait() != 0:
            raise Exception(u"Can't list remote SVN repository. Please make sure the URL is accessible from everywhere!")
        return repo_list

    def _read_progress(self, stream, repo_list, progress_callback):
        factor = 100.0 / len(repo_list)
        files_count = dict((x, i+1) for i, x in enumerate(repo_list))
        while True:
            line = stream.readline()
            if not line:
                break
            if progress_callback:
                try:
                    path = line.split()[1].split(os.path.sep)[0]
                    current = files_count[path]
                    percent = round(current * factor)
                    if percent <= 100:
                        progress_callback(percent)
                except KeyError:
                    pass

    def fetch(self, progress_callback=None):
        if not self.exists():
            os.makedirs(self.repo_path)
            repo_list = self._list_repo()
            proc = subprocess.Popen(["svn", "checkout", self.repo.url, "."] + self.extra_args, env=self.env, cwd=self.repo_path, stdout=subprocess.PIPE)
            self._read_progress(proc.stdout, repo_list, progress_callback)
            if proc.wait() != 0:
                raise Exception(u"Can't import remote SVN repository. Please make sure the URL is accessible from everywhere!")
        else:
            raise Exception(u"Repository already imported")

    def update(self, progress_callback=None):
        if self.exists():
            proc = subprocess.Popen(["svn", "update"] + self.extra_args, env=self.env, cwd=self.repo_path, stdout=subprocess.PIPE)
            output = proc.stdout.read()
            if proc.wait() != 0:
                raise Exception(u"Wrong exit status received from SVN command!")

            if "Updated to" in output:
                self.repo.mark_updated()
        else:
            raise Exception(u"Repository not imported")

    def _diff(self, diff, progress_callback=None):
        if self.exists():
            proc = subprocess.Popen(["svn", "diff", "-rBASE:HEAD", "--summarize"] + self.extra_args, env=self.env, cwd=self.repo_path, stdout=subprocess.PIPE)
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                self._add_to_diff(diff, line, "D", "A", "M")
            if proc.wait() != 0:
                raise Exception(u"Wrong exit status received from SVN command!")
        else:
            raise Exception(u"Repository not imported")

class FileRepo(Repo):
    def __init__(self, repo, user=None, workdir=None, file_path=None):
        super(FileRepo, self).__init__(repo, user, workdir)
        self.file_path = file_path
        self.repo_path = os.path.join(self.workdir, re.sub("[^\w\-_\. ]", "_", self.repo.url))

    def __extract(self):
        if not self.file_path or not os.path.exists(self.file_path):
            raise Exception(u"File archive not found!")
        try:
            if self.exists():
                self.remove()
            try:
                os.makedirs(self.repo_path)
            except OSError, e:
                if e.errno == errno.EEXIST:
                    pass
                else:
                    raise
            patoolib.extract_archive(self.file_path, outdir=self.repo_path)
        except patoolib.util.PatoolError:
            raise Exception(u"Wrong archive file format!")

    def fetch(self, progress_callback=None):
        if not self.exists():
            self.__extract()

    def update(self, progress_callback=None):
        if self.file_path:
            self.__extract()
            self.repo.mark_updated()


class DeploymentKeyProblem(Exception):
    "This exception is thrown when deployment key is not valid anymore"
    pass
