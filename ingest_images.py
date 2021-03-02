# Fall 2020
# Vinetech Image Ingest Script

import os
import argparse


import __init__
from organization import file_org as f_org
from internal import gen_csv, pad_csv, row_pred, bay_pred, rename_files


def parse_args():
    """
    parse_args returns the command line arguments.
    """

    ap = argparse.ArgumentParser()

    ap.add_argument("-v", "--vineyard", default="crawford-beck", help="vineyard name")
    ap.add_argument("-b", "--block", default=9, type=int, help="block number")
    ap.add_argument("-d", "--date", required=True, help="date to ingest (yyyy-mm-dd)")

    ap.add_argument("-r", "--rows", default=21, help="number of rows in block")
    ap.add_argument("-raw_dir", help="directory of unprocessed images")

    ap.add_argument("-s", "--step", type=int, help="step to run")
    ap.add_argument("-db", "--database", action="store_true", help="run db steps")
    ap.add_argument("-reset", help="reset the database, either 'date' or 'all'")

    return ap.parse_args()


def main(args):
    """
    main ingests the images indicated by the passed args object.
    """

    if not args.raw_dir:
        args.raw_dir = f_org.get_image_path(args.vineyard, args.block, args.date)

    if not len(os.listdir(args.raw_dir)):
        print("Chosen path does not contain files")
        print("Make sure to run setup.sh from the root repo")
        return

    # Ingest steps that can be run individually with -s / --step argument
    steps = [
        gen_csv.main,
        pad_csv.main,
        row_pred.main,
        bay_pred.main,
        rename_files.main,
    ]

    # Optionally override the steps with the db loading steps
    if args.database:
        import pandas as pd
        from database import Database as D
        from database import Schema
        from internal.ingest_db import DB_Ingester

        # Connect to the database
        db = D.Database(D.connect())
        db.create_schema(Schema)
        db_loader = DB_Ingester(db)

        if args.reset == "date":
            db.drop_images(args.date)
        elif args.reset == "all":
            db.drop_tables(*D.table_names.values())

        # Override the steps with the db loading steps
        steps = [
            db_loader.add_uuids,
            db_loader.add_bays,
            db_loader.add_metadata,
            db_loader.add_images_to_bays,
            db_loader.add_image_bytes,
            db_loader.add_harvest_data,
        ]

    # Run a single ingest step for debugging
    if args.step is not None:
        print("Running step", args.step)
        steps[args.step](f_org, args)
        return

    # Run all the ingest steps
    df = None
    for s in steps:
        print("Running step", steps.index(s))
        df = s(f_org, args, df=df)


if __name__ == "__main__":
    main(parse_args())
