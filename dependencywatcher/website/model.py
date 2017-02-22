#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

import datetime, bcrypt, string, random, urllib, hashlib, os, errno
from flask import render_template
from flask.ext.login import UserMixin
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from dependencywatcher.version import Version
from dependencywatcher.repo import Repo
from dependencywatcher.db_conf import DBConf
from dependencywatcher.website.webapp import app, db
from dependencywatcher.website.plans import *
from Crypto.PublicKey import RSA
from uuid import uuid4
from collections import OrderedDict
from slugify import slugify
from PIL import Image
from base64 import b64encode
from StringIO import StringIO
from alembic import op

def random_string(length=32):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))

def get_or_create(model, **kwargs):
    instance = db.session.query(model).filter_by(**kwargs).first()
    if instance is not None:
        return instance
    instance = model(**kwargs)
    try:
        db.session.add(instance)
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        instance = db.session.query(model).filter_by(**kwargs).first()
    return instance

def create_if_absent(model, **kwargs):
    if db.session.query(model).filter_by(**kwargs).count() == 0:
        db.session.add(model(**kwargs))
        db.session.flush()

class Avatar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image128 = db.Column(db.LargeBinary)
    image32 = db.Column(db.LargeBinary)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True)

    def _generate_thumbnail(self, size, stream):
        image = Image.open(stream)
        image.thumbnail((size, size), Image.ANTIALIAS)
        s = StringIO()
        image.save(s, "PNG", optimize=True)
        s.seek(0)
        return s.read()

    def update(self, stream):
        self.image128 = self._generate_thumbnail(128, stream)
        stream.seek(0)
        self.image32 = self._generate_thumbnail(32, stream)

    def update_from_url(self, url):
        self.update(StringIO(urllib.urlopen(url).read()))

    def find(self, email):
        self.update_from_url("http://www.gravatar.com/avatar/%s?s=128&d=404" % hashlib.md5(email.lower()).hexdigest())

class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True)
    alerts_NV = db.Column(db.Boolean, default=True)
    unstable_vers = db.Column(db.Boolean, default=False)
    alerts_NL = db.Column(db.Boolean, default=True)
    weekly = db.Column(db.Boolean, default=True)

class KeyPair(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True)
    private = db.Column(db.Text)
    public = db.Column(db.Text)

    def generate(self):
        key = RSA.generate(2048)
        self.private = key.exportKey("PEM")
        self.public = key.publickey().exportKey("OpenSSH")

user_roles = db.Table("user_roles",
    db.Column("role_id", db.Integer, db.ForeignKey("role.id", ondelete="CASCADE")),
    db.Column("user_id", db.Integer, db.ForeignKey("user.id", ondelete="CASCADE")),
    db.UniqueConstraint("role_id", "user_id")
)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(length=64), unique=True, nullable=False)
    description = db.Column(db.Unicode(length=255, collation='utf8_general_ci'))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(length=255))
    email = db.Column(db.Unicode(length=255), unique=True, nullable=False)
    avatar = db.relationship("Avatar", uselist=False)
    avatar_sm = db.Column(db.Text)
    password = db.Column(db.Unicode(length=255))
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    active = db.Column(db.Boolean, nullable=False, default=True)
    activation_code = db.Column(db.String(length=32))
    recovery_code = db.Column(db.String(length=32))
    github = db.Column(db.Text)
    bitbucket = db.Column(db.Text)
    plan = db.Column(db.Integer)
    settings = db.relationship("UserSettings", uselist=False)
    repositories = db.relationship("Repository", backref=db.backref("user", lazy="joined"), lazy="dynamic")
    keypair = db.relationship("KeyPair", uselist=False)
    api_key = db.Column(db.String(length=36))
    roles = db.relationship("Role", secondary=user_roles, lazy="dynamic")
    stats = db.relationship("UserStats", uselist=False)
    stats_prev = db.relationship("UserStatsPrev", uselist=False)
    is_ldap = db.Column(db.Boolean, default=False)

    def __init__(self):
        self.settings = UserSettings()
        self.stats = UserStats()
        self.plan = Plan.ON_PREMISE if DBConf.get().on_premise else Plan.DEVELOPER

    def init(self, name, email, password):
        self.name = name
        self.email = email
        self.set_password(password)
        self.find_avatar()

    def get_plan(self):
        return Plan.by_type(self.plan)

    def set_plan(self, plan):
        self.plan = plan.type

    def get_name(self):
        return self.email if self.name is None else self.name

    def set_password(self, password):
        self.password = unicode(bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()))

    def check_password(self, password):
        if self.password is None:
            return False
        return self.password == unicode(bcrypt.hashpw(password.encode("utf-8"), self.password.encode("utf-8")))

    def is_active(self):
        return self.active

    def has_roles(self, *roles):
        return self.roles.filter(Role.name.in_([unicode(r) for r in roles])).count() > 0

    def update_avatar(self, url=None, image_stream=None):
        old_avatar = self.avatar
        try:
            if self.avatar is None:
                self.avatar = Avatar(user_id=self.id)
            if image_stream is not None:
                self.avatar.update(image_stream)
            elif url is not None:
                self.avatar.update_from_url(url)
            if self.avatar.image32 is not None:
                self.avatar_sm = b64encode(self.avatar.image32)
        except IOError:
            self.avatar = old_avatar

    def find_avatar(self):
        old_avatar = self.avatar
        try:
            if self.avatar is None:
                self.avatar = Avatar(user_id=self.id)
            self.avatar.find(self.email)
            if self.avatar.image32 is not None:
                self.avatar_sm = b64encode(self.avatar.image32)
        except IOError:
            self.avatar = old_avatar

    def update(self, name, email, password=None, image_stream=None):
        self.name = name
        self.email = email
        if password:
            self.set_password(password)
        if image_stream:
            self.update_avatar(image_stream=image_stream)

    def request_activation(self):
        self.active = False
        self.activation_code = random_string()

        from dependencywatcher.tasks import send_email
        send_email.delay(to=[self.email], subject=u"DependencyWatcher Registration Confirmation",
            html=render_template("email/activate.html", user=self))

    def request_recovery(self):
        self.recovery_code = random_string()

        from dependencywatcher.tasks import send_email
        send_email.delay(to=[self.email], subject=u"DependencyWatcher Password Recovery",
            html=render_template("email/recovery.html", user=self))

    def password_reset(self, password):
        self.set_password(password)
        self.recovery_code = None

    def activate(self):
        if not self.active or self.activation_code is not None:
            self.active = True
            self.activation_code = None
            return True
        return False

    def activate_with_code(self, code):
        if self.activation_code == code:
            self.activate()
        else:
            raise Exception(u"Activation code is not correct!")

    def get_repository(self, repo_url):
        return self.repositories.filter_by(url=repo_url, deleted=False).first()

    def get_last_updated_repo(self):
        return self.repositories.filter_by(deleted=False).order_by(Repository.last_update.desc()).first()

    def get_repositories(self):
        return self.repositories.filter_by(deleted=False).all()

    def get_recent_repositories(self, num=7):
        return self.repositories.order_by(Repository.last_view.desc()).limit(num)

    def has_repository(self, repo_url):
        return self.repositories.filter_by(url=repo_url, deleted=False).count() > 0

    def add_repository(self, repo):
        if not Plan.by_type(self.plan).can_add_repo(self, repo):
            raise PlanException(u"Repositories limit is reached")
        if self.has_repository(repo.url):
            raise Exception(u"Repository %s already exists" % repo.url)
        # Delete old repository if exists:
        self.repositories.filter_by(url=repo.url).delete()
        self.repositories.append(repo)

    def delete_repository(self, repo_url):
        repo = self.repositories.filter_by(url=repo_url).first()
        if repo is not None:
            repo.deleted = True
            self.stats.update()
            return True
        return False

    def purge_repositories(self):
        self.repositories.filter_by(deleted=True).delete()

    def restore_repository(self, repo_url):
        repo = self.repositories.filter_by(url=repo_url, deleted=True).first()
        if repo is not None:
            if not Plan.by_type(self.plan).can_add_repo(self, repo):
                raise PlanException(u"Repositories limit is reached")
            repo.deleted = False
            self.stats.update()
            return True
        return False

    def get_workdir(self, create=False):
        workdir = os.path.join(DBConf.get().workdir, self.email)
        if create:
            try:
                os.makedirs(workdir)
            except OSError, e:
                if e.errno == errno.EEXIST:
                    pass
                else:
                    raise
        return workdir

    def generate_key_pair(self, force=False):
        if force or self.keypair is None:
            # Remove old deploy key from repositories:
            if self.keypair is not None:
                self.repositories.filter_by(ssh_key=self.keypair.private).update({Repository.ssh_key: None})
            self.keypair = get_or_create(KeyPair, user_id=self.id)
            self.keypair.generate()
            db.session.commit()

    def generate_api_key(self, force=False):
        if force or self.api_key is None:
            self.api_key = str(uuid4())

    def subscribe_to_lists(self):
        from dependencywatcher.maillist import MailList

        MailList().subscribe_to_all(self.email)
        from dependencywatcher.tasks import send_email
        send_email.delay(to=[self.email], subject=u"Welcome to DependencyWatcher!",
            html=render_template("email/welcome.html", user=self))

    def perform_new_user_actions(self):
        if DBConf.get().on_premise and User.query.count() == 1:
            if User.query.first() == self:
                self.roles.append(Role.query.filter_by(name="admin").first())
        try:
            self.subscribe_to_lists()
        except Exception as e:
            app.logger.exception(e)

class Repository(db.Model):
    GIT = 1
    SVN = 2
    FILE = 3
    MERCURIAL = 4

    AUTH_NONE = 0
    AUTH_CREDENTIALS = 1
    AUTH_PRIVATE_KEY = 2

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"))
    type = db.Column(db.Integer, nullable=False)
    url = db.Column(db.Unicode(length=255), nullable=False, index=True)
    auth_type = db.Column(db.Integer, default=AUTH_NONE)
    username = db.Column(db.Unicode(length=255))
    password = db.Column(db.Unicode(length=255))
    ssh_key = db.Column(db.Text)
    last_update = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_view = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    deleted = db.Column(db.Boolean, default=False)
    fetched = db.Column(db.Boolean, default=False)
    parsed = db.Column(db.Boolean, default=False)
    private = db.Column(db.Boolean, default=False)
    references = db.relationship("DependencyReference", backref=db.backref("repository", lazy="joined"), lazy="dynamic")
    stats = db.relationship("RepositoryStats", uselist=False)

    def __init__(self):
        self.stats = RepositoryStats()

    def mark_updated(self):
        self.last_update = datetime.datetime.utcnow()
        db.session.commit()

    def mark_viewed(self):
        self.last_view = datetime.datetime.utcnow()
        db.session.commit()

    def update_ssh_key(self, ssh_key):
        self.ssh_key = ssh_key
        db.session.commit()

class Dependency(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(length=128), nullable=False)
    description = db.Column(db.Text)
    context = db.Column(db.String(length=64), nullable=False)
    updated = db.Column(db.DateTime)
    version = db.Column(db.Unicode(length=36))
    stable_version = db.Column(db.Unicode(length=36))
    license_id = db.Column(db.Integer, db.ForeignKey("license.id", ondelete="SET NULL"))
    license = db.relationship("License")
    url = db.Column(db.Unicode(length=1024))
    references = db.relationship("DependencyReference", backref=db.backref("dependency", lazy="joined"), lazy="dynamic")
    __table_args__ = (db.UniqueConstraint("name", "context"), )

class License(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(length=255), nullable=False, unique=True)
    normalized = db.Column(db.Unicode(length=255))

class DependencyReference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.Unicode(length=36))
    file = db.Column(db.Unicode(length=255), nullable=False)
    line = db.Column(db.Integer)
    dependency_id = db.Column(db.Integer, db.ForeignKey("dependency.id", ondelete="CASCADE"))
    repository_id = db.Column(db.Integer, db.ForeignKey("repository.id", ondelete="CASCADE"))
    alerts = db.relationship("Alert", backref=db.backref("reference", lazy="joined"), order_by="desc(Alert.created)", lazy="dynamic")
    __table_args__ = (db.UniqueConstraint("file", "dependency_id", "repository_id"), )

    def source_available(self):
        return self.version not in os.path.basename(self.file)

class Alert(db.Model):
    NEW_VERSION = 1
    NEW_LICENSE = 2
    BAD_LICENSE = 3

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Integer, nullable=False)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    sent = db.Column(db.Boolean, default=False)
    fixed = db.Column(db.Boolean, default=False)
    release_type = db.Column(db.Integer)
    reference_id = db.Column(db.Integer, db.ForeignKey("dependency_reference.id", ondelete="CASCADE"), nullable=False)
    __table_args__ = (db.UniqueConstraint("type", "reference_id"), )

post_tags = db.Table("post_tags",
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id", ondelete="CASCADE")),
    db.Column("post_id", db.Integer, db.ForeignKey("blog_post.id", ondelete="CASCADE")),
    db.UniqueConstraint("tag_id", "post_id")
)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(length=64), nullable=False, unique=True)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.Unicode(length=128), index=True)
    author = db.Column(db.Unicode(length=255))
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    title = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.relationship("Tag", secondary=post_tags, backref=db.backref("posts", lazy="dynamic"))

    def make_slug(self):
        self.slug = slugify(self.title, max_length=128)

class StatsMixin(object):
    @declared_attr
    def user_id(cls):
        return db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True)

    id = db.Column(db.Integer, primary_key=True)
    updated = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    deps = db.Column(db.Integer, default=0)
    alerts = db.Column(db.Integer, default=0)
    alerts_f = db.Column(db.Integer, default=0)
    oldver = db.Column(db.Integer, default=0)
    oldver_f = db.Column(db.Integer, default=0)
    oldver_maj = db.Column(db.Integer, default=0)
    oldver_min = db.Column(db.Integer, default=0)
    oldver_bug = db.Column(db.Integer, default=0)
    recommends = db.Column(db.Integer, default=0)
    recommends_f = db.Column(db.Integer, default=0)
    licissues = db.Column(db.Integer, default=0)
    licissues_f = db.Column(db.Integer, default=0)

    def copy_to(self, stats):
        for f in self.__table__.columns.keys():
            if f not in ["id"]:
                setattr(stats, f, getattr(self, f))

class UserStats(db.Model, StatsMixin):
    __tablename__ = "user_stats"

    def update_deps_count(self):
        self.deps = DependencyReference.query.join(DependencyReference.repository) \
            .filter(Repository.user_id == self.user_id, Repository.deleted == False).count()

    def update_alerts_count(self):
        alerts_by_type = db.session.query(Alert.type, Alert.fixed, Alert.release_type, func.count(Alert.type)) \
            .join(Alert.reference).join(DependencyReference.repository) \
                .filter(Repository.user_id == self.user_id, Repository.deleted == False, Alert.read == False) \
                    .group_by(Alert.type, Alert.fixed, Alert.release_type).all()

        self.oldver = 0
        self.oldver_f = 0
        self.licissues = 0
        self.licissues_f = 0
        self.recommends = 0
        self.recommends_f = 0
        self.oldver_maj = 0
        self.oldver_min = 0
        self.oldver_bug = 0

        for type, fixed, release_type, count in alerts_by_type:
            if type == Alert.NEW_VERSION:
                if fixed:
                    self.oldver_f = self.oldver_f + count
                else:
                    self.oldver = self.oldver + count
                    if release_type == Version.REL_MAJOR:
                        self.oldver_maj = self.oldver_maj + count
                    elif release_type == Version.REL_MINOR:
                        self.oldver_min = self.oldver_min + count
                    elif release_type == Version.REL_BUGFIX:
                        self.oldver_bug = self.oldver_bug + count
            elif type == Alert.NEW_LICENSE or type == Alert.BAD_LICENSE:
                if fixed:
                    self.licissues_f = self.licissues_f + count
                else:
                    self.licissues = self.licissues + count

        self.alerts = self.oldver + self.licissues + self.recommends
        self.alerts_f = self.oldver_f + self.licissues_f + self.recommends_f

    def update(self):
        db.session.flush()

        self.update_deps_count()
        self.update_alerts_count()

    def get_license_breakdown(self, num=7):
        licenses = db.session.query(License.normalized, func.count(License.normalized)).join(Dependency.references) \
                .join(DependencyReference.repository).filter(Repository.user_id == self.user_id, Repository.deleted == False) \
                    .group_by(License.normalized).all()

        splice = sorted(licenses, key=lambda x: x[1], reverse=True)[:num]
        other = [(l,n) for l,n in licenses if not l in [s for s,_ in splice]]
        d = OrderedDict(splice)
        other_sum = 0
        for l, n in other:
            other_sum = other_sum + n
        if "Other" in d:
            other_sum = other_sum + d["Other"]
        if other_sum > 0:
            d["Other"] = other_sum
        return d

class UserStatsPrev(db.Model, StatsMixin):
    __tablename__ = "user_stats_prev"

class Config(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    on_premise = db.Column(db.Boolean, default=True)
    workdir = db.Column(db.String(length=255))
    site_url = db.Column(db.Unicode(length=255))
    request_activation = db.Column(db.Boolean, default=False)

    ldap_enabled = db.Column(db.Boolean, default=False)
    ldap_url = db.Column(db.Unicode(length=255))
    ldap_basedn = db.Column(db.Unicode(length=128))

    smtp_server = db.Column(db.Unicode(length=255))
    smtp_use_ssl = db.Column(db.Boolean, default=True)
    smtp_username = db.Column(db.Unicode(length=128))
    smtp_password = db.Column(db.Unicode(length=128))
    smtp_from_addr = db.Column(db.Unicode(length=128))

    github_enabled = db.Column(db.Boolean, default=False)
    github_client_id = db.Column(db.String(length=32))
    github_client_secret = db.Column(db.String(length=64))
    github_scope = db.Column(db.String(length=128))

    bitbucket_enabled = db.Column(db.Boolean, default=False)
    bitbucket_key = db.Column(db.String(length=32))
    bitbucket_secret = db.Column(db.String(length=64))

    mailchimp_enabled = db.Column(db.Boolean, default=False)
    mailchimp_api_key = db.Column(db.String(length=64))
    mailchimp_list_news = db.Column(db.String(length=32))

class RepositoryStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    repository_id = db.Column(db.Integer, db.ForeignKey("repository.id", ondelete="CASCADE"))
    updated = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    deps = db.Column(db.Integer, default=0)
    outdated = db.Column(db.Integer, default=0)

    def update(self):
        refs = DependencyReference.query.join(DependencyReference.repository) \
                .filter(Repository.id == self.repository_id)
        self.deps = refs.count()
        self.outdated = refs.join(DependencyReference.alerts).filter(Alert.type == Alert.NEW_VERSION).count() if self.deps > 0 else 0

