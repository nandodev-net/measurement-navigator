#!/bin/bash
# Use this file to start the production server.
# Possible options:
#   --dev: Create a development container, the user will be root and the code folder will be on synch with your host,
#          this way you can iterate faster
#   --build: rebuild the container instead of just starting it, it's way slower, but it's required in case you want to update changes 
#            to the project.

# Check if should rebuild entire docker 

if [[ $* == *--build* ]] 
then 
    SHOULD_BUILD=$1 
else 
    SHOULD_BUILD="" 
fi


if [[ $* == *--dev* ]] 
then 
    DOCKERCOMPOSE_FILE=docker-compose.dev.yml
    cp ./run_web_service.sh measurement_navigator/vsf
    chmod +x measurement_navigator/vsf/run_web_service.sh
else 
    DOCKERCOMPOSE_FILE=docker-compose.yml 
fi


# Colors
COLOR_NC="$(tput sgr0)" # No Color
COLOR_BLACK='\e[0;30m'
COLOR_GRAY='\e[1;30m'
COLOR_RED='\e[0;31m'
COLOR_LIGHT_RED='\e[1;31m'
COLOR_GREEN='$(tput setaf2)'
COLOR_LIGHT_GREEN='\e[1;32m'
COLOR_BROWN='\e[0;33m'
COLOR_YELLOW='\e[1;33m'
COLOR_BLUE='\e[0;34m'
COLOR_LIGHT_BLUE='\e[1;34m'
COLOR_PURPLE='\e[0;35m'
COLOR_LIGHT_PURPLE='\e[1;35m'
COLOR_CYAN='\e[0;36m'
COLOR_LIGHT_CYAN='\e[1;36m'
COLOR_LIGHT_GRAY='\e[0;37m'
COLOR_WHITE='\e[1;37m'

printf "${COLOR_LIGTH_BLUE}Shutting down active servers...${COLOR_NC}\n" &&\
docker compose -f ${DOCKERCOMPOSE_FILE} down &&\
printf "${COLOR_LIGHT_BLUE}Building docker composer file...${COLOR_NC}\n" &&\
docker compose -f ${DOCKERCOMPOSE_FILE} up -d $SHOULD_BUILD &&\
printf "${COLOR_LIGHT_BLUE}Collecting static files...${COLOR_NC}\n" &&\
docker compose -f ${DOCKERCOMPOSE_FILE} exec --user root web chown -R vsf:vsf ../static &&\
docker compose -f ${DOCKERCOMPOSE_FILE} exec web python manage.py collectstatic --no-input --clear &&\
printf "${COLOR_LIGHT_GREEN}Ready to go!${COLOR_NC}\n" &&\
printf "${COLOR_LIGHT_BLUE}to run migrations, use the following commnad:${COLOR_NC}\n" &&\
printf "${COLOR_YELLOW}   docker compose -f ${DOCKERCOMPOSE_FILE} exec web python manage.py migrate --noinput${COLOR_NC}\n" &&\
printf "${COLOR_LIGHT_BLUE}You can test this server by requesting to ${COLOR_YELLOW}localhost:1337/admin${COLOR_NC}\n" &&\
printf "${COLOR_LIGHT_BLUE}Check the logs using: ${COLOR_YELLOW}docker compose -f ${DOCKERCOMPOSE_FILE} logs -f${COLOR_NC}\n"