#! /bin/bash

date=$1
year=$(echo $1 | cut -d'-' -f1)
label_dir=/srv/projects/vinetech/labels/crawford-beck
harvest_file=$label_dir/harvest_$year.csv
image_dir=/srv/projects/vinetech/images/crawford-beck/block09/$date

location_file=/tmp/locations/$date/locations.csv

if [ -f $harvest_file ]; then
  python3 ../ingest_images.py -db ../db.conf -resize 400 300 -d $date -i $image_dir $harvest_file $location_file
else
  echo $harvest_file harvest file does not exist
  exit 1
fi
