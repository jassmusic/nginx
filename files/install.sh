#!/data/data/com.termux/files/usr/bin/bash

# nginx install
pkg install termux-services
apt -y install nmap sqlite nginx php-fpm

# php-fpm update
#sed -i 's/listen\ =\ \/data\/data\/com.termux\/files\/usr\/var\/run\/php-fpm.sock/listen\ =\ 127.0.0.1:9000/' /data/data/com.termux/files/usr/etc/php-fpm.d/www.conf

# nginx conf update
#cd /data/data/com.termux/files/usr/etc/nginx
#curl -LO https://raw.githubusercontent.com/jassmusic/termux/master/nginx.conf
cp ~/app/data/custom/nginx/files/nginx.conf /data/data/com.termux/files/usr/etc/nginx

# make nginx dir
mkdir -p ~/app/data/nginx
mkdir -p ~/app/data/nginx/www
cd ~/app/data/nginx
ln -s /data/data/com.termux/files/usr/etc/nginx/nginx.conf nginx.conf
cp ~/app/data/custom/nginx/files/php.ini ~/app/data/nginx
cp ~/app/data/custom/nginx/files/index.html ~/app/data/nginx/www
cp ~/app/data/custom/nginx/files/phpinfo.php ~/app/data/nginx/www
cp ~/app/data/custom/nginx/files/guide.php ~/app/data/nginx/www

# make pre_start
cd ~/app
cat <<EOF >pre_start.sh
#!/data/data/com.termux/files/usr/bin/bash
sv up nginx
sv up php-fpm
EOF
chmod +x pre_start.sh

chmod 777 -R ~/app/data/nginx
