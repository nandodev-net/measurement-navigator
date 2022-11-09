#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $VSF_DB_HOST $VSF_DB_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi


exec "$@"