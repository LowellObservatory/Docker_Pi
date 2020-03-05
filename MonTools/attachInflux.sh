#!/bin/bash

docker-compose up -d influxdb; docker exec -it influxdb influx
