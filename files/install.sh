#!/bin/sh
mkdir -p /app/data/nginx
mkdir -p /app/data/nginx/www
apk update
apk upgrade
apk add nginx
mkdir -p /run/nginx
mv /etc/nginx/nginx.conf /etc/nginx/nginx.conf.orig
cp /app/data/custom/nginx/files/nginx.conf /app/data/nginx/nginx.conf
ln -s /app/data/nginx/nginx.conf /etc/nginx/nginx.conf
apk add php7-fpm php7-mcrypt php7-soap php7-openssl php7-gmp php7-pdo_odbc php7-json php7-dom php7-pdo php7-zip php7-mysqli php7-sqlite3 php7-apcu php7-pdo_pgsql php7-bcmath php7-gd php7-odbc php7-pdo_mysql php7-pdo_sqlite php7-gettext php7-xmlreader php7-xmlrpc php7-bz2 php7-iconv php7-pdo_dblib php7-curl php7-ctype php7-simplexml php7-mbstring php7-fileinfo php7-session
mv /etc/php7/php.ini /etc/php7/php.ini.orig
cp /app/data/custom/nginx/files/php.ini /app/data/nginx/php.ini
ln -s /app/data/nginx/php.ini /etc/php7/php.ini
cp /app/data/custom/nginx/files/pre_start.sh /app/pre_start.sh
cp /app/data/custom/nginx/files/index.html /app/data/nginx/www/index.html
cp /app/data/custom/nginx/files/phpinfo.php /app/data/nginx/www/phpinfo.php
cp /app/data/custom/nginx/files/guide.php /app/data/nginx/www/guide.php
chmod 777 -R /app/data/nginx
