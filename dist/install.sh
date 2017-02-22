#!/bin/bash
#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

if [ $(id -u) -ne 0 ]; then
	echo " * This script must be run as root!" >&2
	exit 1
fi
if selinuxenabled >/dev/null 2>&1; then
	echo " * SELinux must be disabled!" >&2
	exit 1
fi
if ! which docker >/dev/null 2>&1; then
	echo " * Docker is not installed!" >&2
	exit 1
fi
if ! docker info >/dev/null 2>&1; then
	echo " * Docker is not running!" >&2
	exit 1
fi
if ! docker create --help 2>/dev/null | grep "\-publish" >/dev/null; then
	echo " * Docker of version 1.5 and greater is required!"
	exit 1
fi

image=dependencywatcher
container=dependencywatcher_service

cd .install || exit 1

docker build -t $image . || exit 1

docker rmi -f $(docker images --filter "dangling=true" -q) 2>/dev/null

docker rm -f $container 2>/dev/null

docker create -p 3001:3001 \
	-v /var/lib/dependencywatcher/workspace:/var/lib/dw-workspace \
	--name $container $image || exit 1

echo
echo " ===================================== "
echo "  DependencyWatcher is now installed!  "
echo " ===================================== "
echo

