#!/bin/sh

if [ $1 == 'password*' ] then
  exec echo "$GIT_ASKPASS_PASSWORD"
  exit 0;
fi

if [ $1 == 'username*' ] then
  exec echo "$GIT_ASKPASS_USERNAME"
  exit 0;
fi
