#!/bin/bash

#the input/output variables
date=$1
base_dir=/srv/projects/vinetech/images/crawford-beck/block09/
img_dir=$base_dir/$date
out_dir=/tmp/locations/$date

#labeled data, static
labeled=/srv/projects/vinetech/labels/crawford-beck/2019-06-12/locations.csv

mkdir -p $out_dir

python3 ../build_locations.py -i $img_dir -d $date -l $labeled -o $out_dir | tee $out_dir/out.txt

