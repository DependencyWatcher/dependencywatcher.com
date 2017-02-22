#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from celery import Celery, current_task
from celery.schedules import timedelta
from dependencywatcher.smtp import SMTPMailer
from dependencywatcher.repo import Repo
from dependencywatcher.db_conf import DBConf
from dependencywatcher.manifests import Manifests
from dependencywatcher.website.webapp import app, db
from dependencywatcher.parser.parser import Parser
from dependencywatcher.crawler.updates import UpdateFinder
from multiprocessing.pool import ThreadPool
from flask import render_template
from copy import deepcopy
from datetime import datetime, timedelta
import os

update_finder = UpdateFinder()

def init_settings(app):
    app.config.update({
        "CELERY_RESULT_BACKEND": "db+" + app.config["SQLALCHEMY_DATABASE_URI"],
        "CELERY_TASK_SERIALIZER": "json",
        "CELERY_RESULT_SERIALIZER": "json",
        "CELERY_ACCEPT_CONTENT": ["json"],
        "CELERY_TASK_RESULT_EXPIRES": 3600,
        "CELERYBEAT_SCHEDULE": {
            "parse-all": {
                "task": "dependencywatcher.tasks.parse_all",
                "schedule": timedelta(minutes=30)
            },
            "sync-manifests": {
                "task": "dependencywatcher.tasks.sync_manifests",
                "schedule": timedelta(minutes=30)
            },
            "find-updates": {
                "task": "dependencywatcher.tasks.find_all_updates",
                "schedule": timedelta(minutes=30)
            },
            "deliver-alerts": {
                "task": "dependencywatcher.tasks.send_alerts",
                "schedule": timedelta(hours=1)
            },
            "generate-weekly-reports": {
                "task": "dependencywatcher.tasks.send_weekly_report",
                "schedule": timedelta(hours=1)
            }
        }
    })

# http://flask.pocoo.org/docs/patterns/celery/#configuring-celery
def make_celery(app):
    init_settings(app)
    celery = Celery(app.import_name, broker=app.config["CELERY_BROKER_URL"])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

celery = make_celery(app)

@celery.task(bind=True, ignore_result=True)
def send_email(self, **kwargs):
    SMTPMailer().send(**kwargs)

@celery.task(bind=True)
def fetch_repository(self, user_email, repo_url):
    from dependencywatcher.website.model import User

    user = User.query.filter_by(email=unicode(user_email)).first()
    if user is not None:
        repository = user.get_repository(repo_url)
        if repository:
            def progress_callback(progress):
                current_task.update_state(state="PROGRESS", meta={"progress": progress})
            try:
                Repo.create(user=user, repo=repository).fetch_or_update(progress_callback=progress_callback)
                repository.fetched = True

                post_fetch_tasks.delay(user.email, repo_url)
                db.session.commit()
            except Exception as e:
                app.logger.exception("Error importing repository: %s" % repo_url)
                db.session.rollback()

                user.delete_repository(repo_url)
                db.session.commit()
                raise e

def parse_repository(repo):
    """ Parse single user repository, and find used dependencies """
    from dependencywatcher.website.model import DependencyReference, Dependency, get_or_create

    references = []
    try:
        for d in Parser.parse_dir(repo.repo_path):
            name = d["name"].encode("utf-8")
            version = d["version"].encode("utf-8")
            context = d["context"].encode("utf-8")
            file = d["file"][len(repo.repo_path)+1:].encode("utf-8")
            if len(file) > 255:
                file = file[len(file)-255:]

            dependency = get_or_create(Dependency, name=unicode(name), context=context)

            reference = get_or_create(DependencyReference, file=unicode(file), \
                dependency_id=dependency.id, repository_id=repo.repo.id)

            reference.dependency = dependency
            reference.version = unicode(version)

            if "line" in d:
                reference.line = int(d["line"])

            references.append(reference)

        repo.repo.parsed = True

        existing_ids = [r.id for r in references]
        if len(existing_ids) > 0:
            DependencyReference.query.filter(DependencyReference.repository_id == repo.repo.id, \
                ~DependencyReference.id.in_(existing_ids)).delete(synchronize_session=False)
        else:
            DependencyReference.query.filter(DependencyReference.repository_id == repo.repo.id) \
                .delete(synchronize_session=False)

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        app.logger.exception(e)

    return references

def find_updates(dependencies):
    from dependencywatcher.website.model import License, get_or_create
    from dependencywatcher.alerts import AlertsGenerator
    import dependencywatcher.license
    
    updates = []
    workdir = DBConf.get().workdir
    def find_updates_thread(dependency):
        try:
            manifest = Manifests(workdir).load(dependency.name)
            update = update_finder.find_update(manifest if manifest is not None else dependency.name, dependency.context)
            if update is not None:
                updates.append((dependency, update))
        except Exception as e:
            app.logger.warning("Can't find update for: %s" % dependency.name)
    
    pool = ThreadPool(processes=10)
    for dependency in dependencies:
        pool.apply_async(find_updates_thread, args=(dependency,))
    pool.close()
    pool.join()

    users = {}
    repositories = {}

    for dependency, update in updates:
        prev_info = {}
        if dependency.version is not None:
            prev_info["version"] = dependency.version
        if dependency.stable_version is not None:
            prev_info["stable_version"] = dependency.stable_version
        if dependency.license is not None:
            prev_info["license"] = dependency.license.name

        if "license" in update and update["license"]:
            dependency.license = get_or_create(License, name=unicode(update["license"].encode("utf-8")))
            if dependency.license.normalized is None:
                dependency.license.normalized = unicode(dependencywatcher.license.License(dependency.license.name).normalized)

        if "description" in update and update["description"]:
            dependency.description = unicode(update["description"].encode("utf-8"))

        if "updatetime" in update and update["updatetime"]:
            dependency.updated = datetime.fromtimestamp(update["updatetime"] / 1000.0)

        if "url" in update and update["url"]:
            dependency.url = unicode(update["url"].encode("utf-8"))

        if "stable_version" in update and update["stable_version"]:
            dependency.stable_version = unicode(update["stable_version"])

        dependency.version = unicode(update["version"])

        db.session.flush()

        AlertsGenerator().generate(prev_info, dependency)

        for reference in dependency.references:
            users[reference.repository.user.id] = reference.repository.user
            repositories[reference.repository.id] = reference.repository

    for user in users.itervalues():
        user.stats.update()

    for repo in repositories.itervalues():
        repo.stats.update()

    db.session.commit()

@celery.task(bind=True, ignore_result=True)
def post_fetch_tasks(self, user_email, repo_url):
    """ Parses newly fetched repository """
    from dependencywatcher.website.model import User

    user = User.query.filter_by(email=unicode(user_email)).first()
    if user is not None:
        repo = user.get_repository(repo_url)
        if repo is not None:
            references = parse_repository(Repo.create(user=user, repo=repo))
            unique_dep_names = set()
            dependencies = [reference.dependency for reference in references \
                if reference.dependency.name not in unique_dep_names and \
                    not unique_dep_names.add(reference.dependency.name)]
            find_updates(dependencies)

        user.stats.update()
        repo.stats.update()

        db.session.commit()

@celery.task(bind=True, ignore_result=True)
def parse_all(self):
    """ Parses all user repositories, and find all used dependencies """
    from dependencywatcher.website.model import Repository, UserStats

    user_id = None
    for repository in Repository.query.filter_by(parsed=True, deleted=False).order_by(Repository.user_id).all():
        repo = Repo.create(user=repository.user, repo=repository)
        repo.fetch_or_update()
        parse_repository(repo)

        if user_id is None or user_id != repository.user_id:
            repository.user.stats.update()
            user_id = repository.user_id

        repository.stats.update()

        db.session.commit()

@celery.task(bind=True, ignore_result=True)
def sync_manifests(self):
    workdir = DBConf.get().workdir
    Manifests(workdir).sync()

@celery.task(bind=True, ignore_result=True)
def find_all_updates(self):
    from dependencywatcher.website.model import Dependency
    find_updates(Dependency.query.all())

@celery.task(bind=True, ignore_result=True)
def send_alerts(self):
    """ Deliver new alerts to user """
    from dependencywatcher.website.model import User, Alert, DependencyReference, Repository
    from dependencywatcher.tasks import send_email
    from dependencywatcher.version import Version
    
    for user in User.query.all():
        cursor = Alert.query.filter(Alert.sent == False, Alert.fixed == False) \
            .join(Alert.reference).join(DependencyReference.repository) \
                .filter(Repository.user_id == user.id, Repository.deleted == False)

        filter_types = []
        if not user.settings.alerts_NV:
            filter_types.append(Alert.NEW_VERSION)
        if not user.settings.alerts_NL:
            filter_types.extend([Alert.NEW_LICENSE, Alert.BAD_LICENSE])
        if len(filter_types) > 0:
            cursor = cursor.filter(Alert.type.notin_(filter_types))

        if cursor.count() > 0:
            alerts = cursor.all()
            send_email.delay(to=[user.email], subject=u"New Alerts", \
                html=render_template("email/alerts.html", alerts=alerts, user=user, Version=Version))
            for alert in alerts:
		app.logger.debug("Marking alert %s as sent" % alert.__dict__)
                alert.sent = True
            db.session.commit()

@celery.task(bind=True, ignore_result=True)
def send_weekly_report(self):
    """ Generate weekly report and schedule delivering it """
    from dependencywatcher.website.model import User, UserSettings, UserStats, UserStatsPrev
    from dependencywatcher.tasks import send_email
    from dependencywatcher.reports.weekly import WeeklyReport

    period_end = datetime.now()
    period_start = period_end - timedelta(7)

    query = ((UserSettings.weekly == True) & ((User.stats_prev == None) | ((UserStatsPrev.updated < period_start) & (UserStatsPrev.updated < UserStats.updated))))
    for user in User.query.join(User.settings).join(User.stats).outerjoin(User.stats_prev).filter(query).all():
        try:
            file = os.path.join(user.get_workdir(True), "Weekly_Report.pdf")
            WeeklyReport(file=file, period_start=period_start, period_end=period_end, user=user).generate()

            send_email.delay(to=[user.email], subject=u"Weekly Report", \
                files=[file], html=render_template("email/weekly.html", user=user))

            # Copy current statistics to weekly
            if user.stats_prev is None:
                user.stats_prev = UserStatsPrev(user_id=user.id)
                db.session.add(user.stats_prev)

            user.stats.copy_to(user.stats_prev)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            app.logger.exception(e)

