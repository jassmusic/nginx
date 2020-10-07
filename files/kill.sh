#!/bin/sh
nginx -s stop
ps -eo pid,args | grep php-fpm7 | grep -v grep | awk '{print $1}' | xargs -r kill -9
