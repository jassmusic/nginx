#!/data/data/com.termux/files/usr/bin/bash
sv down nginx
sv down php-fpm
apt -y remove nginx php-fpm
rm -rf ~/app/pre_start.sh
rm -rf ~/app/data/nginx/www/index.html
rm -rf ~/app/data/nginx/www/phpinfo.php
rm -rf ~/app/data/nginx/www/manual.php
