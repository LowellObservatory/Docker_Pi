#!/bin/bash

# Depends on the bind mounts specified in the .env file
#  to actually access the influxdb data in the right place!

source ./.env

if [ -z "$INFLUXDB_VERSION" ]
then
    INFLUXDB_VERSION='latest'
fi

if [ -z "$DCDATADIR" ]
then
    DCDATADIR="$HOME/DockerData"
fi

if [ -z "$DCDEVDIR" ]
then
    DCDEVDIR="$HOME/DockerDev/DCTStack/"
fi

outdir="$DCDEVDIR/influxbackupdump"
if [ -d "$outdir" ]
then
    echo "Good, $outdir exists for backup output"
else
    mkdir "$outdir"
fi

bstr="docker exec -it influxdb influxd backup -portable /home/influxbackups"
rstr="docker-compose up -d influxdb; docker exec -it influxdb influxd restore -portable /home/influxbackups"

echo "Copy and run this command to BACKUP; influxdb container should be running!"
echo ""
echo "$bstr"
echo ""
echo "Copy and run this command to RESTORE; influxdb container should be running!"
echo ""
echo "$rstr"
echo ""
