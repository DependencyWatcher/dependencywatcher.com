#!/bin/bash -x

TARGET=dependencywatcher-docker
if [ $1 = "release" ]; then
	TARGET=$TARGET-$(date +"v%Y%m%d")
fi
TARGET_INSTALL=$TARGET/.install
rm -rf $TARGET
mkdir -p $TARGET_INSTALL/dependencywatcher || exit 1

cp -aL ../dependencywatcher ../migrations ../manage.py ../setup.py $TARGET_INSTALL/dependencywatcher/ || exit 1
cp run.sh $TARGET_INSTALL/dependencywatcher/ || exit 1
cp Dockerfile supervisor.conf $TARGET_INSTALL/ || exit 1

key=`python -c "import os; print os.urandom(24).encode('hex');"` || exit 1
cat config.py | sed "s/^SECRET_KEY.*/SECRET_KEY = \"$key\"/" > $TARGET_INSTALL/dependencywatcher/config.py || exit 1

find $TARGET_INSTALL/ -name "*.pyc" -delete || exit 1

rm $TARGET_INSTALL/dependencywatcher/dependencywatcher/website/templates/profile_plan.html || exit 1
rm $TARGET_INSTALL/dependencywatcher/dependencywatcher/website/templates/upgrade.html || exit 1
rm $TARGET_INSTALL/dependencywatcher/dependencywatcher/website/views/upgrade.py || exit 1
rm $TARGET_INSTALL/dependencywatcher/dependencywatcher/website/templates/index.html || exit 1
rm $TARGET_INSTALL/dependencywatcher/dependencywatcher/website/templates/blog_post.html || exit 1
rm $TARGET_INSTALL/dependencywatcher/dependencywatcher/website/templates/blog.html || exit 1
rm $TARGET_INSTALL/dependencywatcher/dependencywatcher/website/views/blog.py || exit 1
rm $TARGET_INSTALL/dependencywatcher/dependencywatcher/website/static/css/pagedown.min.css || exit 1
rm $TARGET_INSTALL/dependencywatcher/dependencywatcher/website/static/css/pagedown.css || exit 1

for i in `find $TARGET_INSTALL/dependencywatcher/dependencywatcher -name "*.min.*"`; do
	rm `echo $i | sed 's/\.min//'` || exit 1
done

cp README.md install.sh start.sh stop.sh $TARGET/ || exit 1

rm -f $TARGET.tgz
tar -zcf $TARGET.tgz $TARGET/ || exit 1
rm -rf $TARGET/

