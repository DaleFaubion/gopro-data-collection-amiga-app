## Ingest

There are two primary ingest steps, the first generates a set of csvs from images that are dumped into directories on HPC, the second uses the csvs to load images into the database. The database is currently only a POC and doesn't implement close to all of the designed features.

The current schema can be found [here](https://gitlab.com/georgefox/engr/senior-design/vinetech-data-processing/database/-/blob/master/schema.sql).


## Initial Ingest (JPG -> CSV)

To generate a `csv` from a date of `jpg` files, run
```cmd
python ingest_images.py -v <vineyard> -b <block> -d <date>
```

If the ingest indicates that the gps data is corrupted, you can perform individual steps of the ingest by passing the `-s` flag with the step number to run.
The date with hand-labeled data with row/bay labels is '2019-06-12'.

## Database Ingest (CSV -> DB)

To ingest a date of images from a `csv` into the database, run
```cmd
python ingest_images.py -v <vineyard> -b <block> -d <date> -db
```

If the ingest fails or should be restarted, the `-reset` command can be passed, and the same `-s` flag can be used to run specific steps of the ingest.

### Ingest Testing

There are ci and unit tests that run with `sh test.sh` (using the conda environment specified in `environment.yml` or the general `vinetech` environment defined in the root repo). Additionally, the `gps_model_selection` and `bay_model_selection` scripts can be used to test new bay prediction and gps data correction models.

While writing up this documentation I ran into a problem where after months of passing tests, they now fail. It had to do with a package dependency update: the CI runner was using pillow 8.2.0 and I had 8.0.0 installed. In the release notes they noted a change to `getexif()` and that `_getexif()` behaved as before. ... check your dependencies if things start breaking!!

### Database Schema Development

The original schema can be found in the relics directory, the one developed in 2020 can be found in the 2020_Schema directory, and the one currently being used in the POC can be found [here](https://gitlab.com/georgefox/engr/senior-design/vinetech-data-processing/database/-/blob/master/schema.sql).
