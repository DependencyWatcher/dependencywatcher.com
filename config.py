#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

SQLALCHEMY_DATABASE_URI = "mysql+mysqldb://dw:dw@localhost/dw?charset=utf8"
CELERY_BROKER_URL = "amqp://guest@127.0.0.1//"
SECRET_KEY = "c677e2ce6885d4a3cb28fc5c18e8e8342f13922ca6330a7a"
#SQLALCHEMY_ECHO = True
SQLALCHEMY_TRACK_MODIFICATIONS = False

#SQLALCHEMY_DATABASE_URI = "sqlite:////var/lib/dw-workspace/db.sqlite"
#CELERY_BROKER_URL = "sqla+" + SQLALCHEMY_DATABASE_URI
