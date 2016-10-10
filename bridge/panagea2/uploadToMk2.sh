#!/bin/sh

HOST='192.168.0.20'
USER='root'
PASSWD=''
FILE='bridge'
TARGET='/mnt/ubi/etsi'

ftp -n $HOST <<END_SCRIPT
quote USER $USER
quote PASS $PASSWD
cd $TARGET
bin
put $FILE
quit
END_SCRIPT
exit 0


