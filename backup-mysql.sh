#!/bin/sh

tmpfile=/tmp/dw-mysql.sql.gz
mysqldump -u dw -pdw dw | gzip - > $tmpfile && ./dropbox-upload.py $tmpfile
s=$?
rm -f $tmpfile
exit $s

