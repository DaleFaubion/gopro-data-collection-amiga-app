## Ingest

There are two primary ingest steps, the first generates a set of csvs from images, the second uses the csvs to load images into the database. 

The current schema can be found [here](https://gitlab.com/georgefox/engr/senior-design/vinetech-data-processing/database/-/blob/master/schema.sql).


## Initial Ingest (JPG -> CSV)

To generate a `csv` from a date of `jpg` files, run
```cmd
python3 build_locations.py -i IMAGE_DIR -d DATE -l LABELED_DATA
```

The script fixes corrupted GPS data by training a model on hand-labeled data. 
Bays are also predicted with an ML model and the rows are assigned with a clustering algorithm.
The date with hand-labeled data with row/bay labels is '2019-06-12'.

## Database Ingest (CSV -> DB)

To ingest a date of images from a `csv` into the database, run
```cmd
python ingest_images.py -d DATE [-i IMAGE_DIR] [-db DB_CONF] harvest_file location_file
```
