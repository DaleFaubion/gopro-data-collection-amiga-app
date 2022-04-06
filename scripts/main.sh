#!/bin/bash

DIR=/srv/projects/vinetech/images/crawford-beck/block09
EXCLUDE=(2019-06-05 2020-06-26)


# Get database password
echo -n Enter database password: 
read -s PG_PWD
echo

export PGPASSWORD=$PG_PWD

# Drop tables
psql -U vinetech -f ../database/drop.sql

# Re-create tables
psql -U vinetech -f ../database/schema.sql

for f in $DIR/*; do
  date=$(basename $f)

  if ! [[ ${EXCLUDE[*]} =~ "$date" ]]; then
      echo "------ Ingesting date $date ------"

      # If date is from 2019, then use the location file
      # stored in the projects folder
      if ! [[ $f =~ "2019" ]]; then
          echo "-- Running Build Locations --"
          ./build_locs.sh "$date"
      fi

      echo "-- Running Ingest --"
      ./ingest.sh "$date"
  fi

done
