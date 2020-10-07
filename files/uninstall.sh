#!/bin/sh
rm -rf /app/pre_start.sh
rm -rf /app/data/nginx/www/index.html
rm -rf /app/data/nginx/www/phpinfo.php
rm -rf /app/data/nginx/www/manual.php
rm -rf /etc/php7/php.ini
rm -rf /etc/nginx/nginx.conf
apk del php7-fpm php7-mcrypt php7-soap php7-openssl php7-gmp php7-pdo_odbc php7-json php7-dom php7-pdo php7-zip php7-mysqli php7-sqlite3 php7-apcu php7-pdo_pgsql php7-bcmath php7-gd php7-odbc php7-pdo_mysql php7-pdo_sqlite php7-gettext php7-xmlreader php7-xmlrpc php7-bz2 php7-iconv php7-pdo_dblib php7-curl php7-ctype php7-simplexml php7-mbstring php7-fileinfo php7-session
apk del nginx
