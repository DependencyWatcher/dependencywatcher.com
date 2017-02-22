#!/bin/bash
#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

if [ $(id -u) -ne 0 ]; then
	echo " * This script must be run as root!" >&2
	exit 1
fi
if [ ! -d /var/lib/dependencywatcher ] || ! docker ps -a | grep dependencywatcher_service >/dev/null; then
	echo " * DependencyWatcher is not installed! Please run ./install.sh"
	exit 1
fi

docker start dependencywatcher_service >/dev/null || exit 1

echo
echo " ============================================= "
echo "  Started listening on http://localhost:3001/  "
echo " ============================================= "
echo
