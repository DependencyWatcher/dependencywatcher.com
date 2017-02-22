FROM debian:wheezy
MAINTAINER Michael Spector <michael@dependencywatcher.com>

RUN apt-get -y update && apt-get install -y \
		libffi-dev \
		libjpeg8-dev \
		zlib1g-dev \
		supervisor \
		git \
		subversion \
		python-pkg-resources \
		python-dev \
		python-pip \
		python-setuptools \
		python-dateutil \
		python-lxml \
		python-crypto \
		python-ldap \
	&& apt-get clean && apt-get purge && rm -rf /var/lib/apt/lists \
	&& rm -rf /usr/share/doc/* && rm -rf /usr/share/locale/* && rm -rf /usr/share/X11 \
	&& mkdir /var/lib/dw-workspace

ADD dependencywatcher /var/www/dependencywatcher/
RUN pip install -e /var/www/dependencywatcher/
ADD supervisor.conf /etc/supervisor/conf.d/dependencywatcher.conf

EXPOSE 3001

CMD chown -R www-data:www-data /var/lib/dw-workspace \
	&& /usr/bin/supervisord -c /etc/supervisor/supervisord.conf

