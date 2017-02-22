#!/bin/sh -x

if ! which curl 2>&1 >/dev/null; then
	echo " * You must have cURL installed!"
	exit 1
fi

url="{{ config().site_url }}/api/v1/repository/{{ encodeURIComponent(repo_name) }}"

tmpfile=$(tempfile -s .tgz) && rm -f $tmpfile || exit 1
trap "rm -f $tmpfile" INT TERM EXIT

tar -zcf $tmpfile --exclude-vcs . || exit 1

curl -sS -X PUT \
	-H "Authorization: apikey={{ current_user.api_key }}" \
	-F "file=@$tmpfile" \
	"$url" || exit 1

echo
echo " ======================================== "
echo "  Project synchronization was successful  "
echo " ======================================== "
echo
