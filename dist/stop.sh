#!/bin/bash
#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

if [ $(id -u) -ne 0 ]; then
	echo " * This script must be run as root!" >&2
	exit 1
fi

docker stop -t 0 dependencywatcher_service >/dev/null 2>&1

echo
echo " ============================== "
echo "  DependencyWatcher is stopped  "
echo " ============================== "
echo
