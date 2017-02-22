#!/bin/sh

./manage.py db upgrade && exec ./manage.py runserver --threaded

