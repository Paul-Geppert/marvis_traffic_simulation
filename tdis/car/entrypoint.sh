#!/bin/sh

echo "CAR started"

until ip a show v2x &> /dev/null
do
  echo 'waiting for network connection ...'
  sleep 1
done

exec "$@"
