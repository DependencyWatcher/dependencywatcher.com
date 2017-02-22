Website
=======

This project contains the source code and the content of [dependencywatcher.com](dependencywatcher.com) Website.


### Prerequisites ###

#### Install OS dependencies ####

```
sudo apt-get -y update && sudo apt-get install -y \
	python-pkg-resources \
	python-dev \
	python-setuptools \
	build-essential \
	libffi-dev \
	python-dateutil \
	python-lxml \
	python-crypto \
	python-ldap \
	libjpeg8-dev \
	zlib1g-dev \
	rabbitmq-server \
	mysql-server \
	libmysqlclient-dev \
	python-pip \
	git \
	subversion
```

#### Install Python dependencies ####

```
sudo pip install -e .
sudo pip install MySQL-python
```

#### Configure DB ####

```
mysqladmin -u root password admin
cat <<EOF | mysql -uroot -padmin 
CREATE DATABASE dw;
CREATE USER 'dw'@'localhost' IDENTIFIED BY 'dw';
GRANT ALL PRIVILEGES ON *.* TO 'dw'@'localhost';
FLUSH PRIVILEGES;
EOF
```

#### Configure RabbitMQ ####

```
cat >/etc/rabbitmq/rabbitmq.config <<EOF
[
    {rabbit, [{tcp_listeners, [{"127.0.0.1", 5672}]}]}
].
EOF

sudo service rabbitmq-server restart
```

### Running ###

For debugging purposes, run:

 `./manage.py runserver -d

The Website will start serving requests on: http://127.0.0.1:3001/


