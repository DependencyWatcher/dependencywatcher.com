#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

SQLALCHEMY_DATABASE_URI = "sqlite:////var/lib/dw-workspace/db.sqlite"
CELERY_BROKER_URL = "sqla+" + SQLALCHEMY_DATABASE_URI
SECRET_KEY = ""

