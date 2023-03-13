#!/bin/bash
# Use this file to stop the production server

if [[ $* == *--dev* ]] 
then 
    DOCKERCOMPOSE_FILE=docker-compose.dev.yml
else 
    DOCKERCOMPOSE_FILE=docker-compose.yml 
fi


docker-compose -f ${DOCKERCOMPOSE_FILE} down