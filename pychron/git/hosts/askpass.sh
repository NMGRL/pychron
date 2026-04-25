#!/bin/sh
case "$1" in
Username*) echo "${GIT_ASKPASS_USERNAME}" ;;
Password*) echo "${GIT_ASKPASS_PASSWORD}" ;;
esac
#echo $1
#if [ $1 == 'password' ]
#then
#  echo "asdfsdfasd"
#  exec echo "$GIT_ASKPASS_PASSWORD"
#  exit 0
#fi
#
#if [ $1 == 'username*' ]
#then
#  exec echo "$GIT_ASKPASS_USERNAME"
#  exit 0
#fi
