#!/bin/bash

DIR=/srv/projects/vinetech/images/crawford-beck/block09
EXCLUDE=(2019-06-05)

for f in $DIR/*; do
  date=$(basename $f)

  if ! [[ ${EXCLUDE[*]} =~ "$date" ]]; then
    echo "Ingesting date $date"

    echo "-- Running Build Locations --"
    ./build_locs.sh "$date"

    echo "-- Running Ingest --"
    ./ingest.sh "$date"

  fi

done
