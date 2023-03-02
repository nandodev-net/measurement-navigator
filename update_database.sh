#!/bin/bash
# Use this script to run make migrations, migrate, load initial data (fixtures) and crete cache table
docker compose -f docker-compose.yml exec web python manage.py createcachetable
docker compose -f docker-compose.yml exec web python manage.py makemigrations 
docker compose -f docker-compose.yml exec web python manage.py migrate 
