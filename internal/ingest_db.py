# Spring 2020
# Vinetech Database Ingest
# Ingest Step 5

import os
import pandas as pd
import itertools as it
import uuid

from .common import *


class DB_Ingester:
    def __init__(self, db):
        self.db = db

    def add_bays(self, f_org, args, df=None):
        # Open the current csv
        label_file = f_org.get_label_file(args.vineyard, args.block, args.date)
        if df is None:
            df = pd.read_csv(label_file, index_col=False)

        # Ensure all the database bays exist
        bays = df["bay"].unique()
        pred_bays = df["pred_bay"].unique()
        bays = set((*set(bays), *set(pred_bays)))
        rows = df["row"].unique()
        all_bays = it.product(rows, bays)

        # Add the row/bay pairs to the db
        self.db.add_bays(args.vineyard, args.block, all_bays)

        # Save and return
        df.to_csv(label_file, index=False)
        return df

    def add_uuids(self, f_org, args, df=None):
        # Open the current csv
        label_file = f_org.get_label_file(args.vineyard, args.block, args.date)
        if df is None:
            df = pd.read_csv(label_file, index_col=False)

        # Fill in any missing image column data
        if not "image_id" in df.columns:
            df["image_id"] = [str(uuid.uuid4()) for _ in df.index]
        else:
            missing = df[df["image_id"].isnull()].index
            df.loc[missing, "image_id"] = [str(uuid.uuid4()) for _ in missing]

        # Save and return
        df.to_csv(label_file, index=False)
        return df

    def add_metadata(self, f_org, args, df=None):
        # Open the current csv
        label_file = f_org.get_label_file(args.vineyard, args.block, args.date)
        if df is None:
            df = pd.read_csv(label_file, index_col=False)

        # Get the image data that is to be loaded
        entries = ["image_id", "date", "time", "lat", "lon", "angle", "camera"]
        entries = list(df[entries].to_records(index=False))

        # Add the image metadata to the database
        self.db.add_images(entries)

        # Save and return
        df.to_csv(label_file, index=False)
        return df

    def add_images_to_bays(self, f_org, args, df=None):
        # Open the current csv
        label_file = f_org.get_label_file(args.vineyard, args.block, args.date)
        if df is None:
            df = pd.read_csv(label_file, index_col=False)

        # Add the predicted bays
        valid = df[df["pred_bay"].notna()].index
        entries = list(df.loc[valid, ["row", "pred_bay", "id"]].to_records(index=False))
        self.db.add_images_to_bays(args.vineyard, args.block, "true", "pred", entries)

        # Add the real bays (if they exist...)
        valid = df[df["bay"].notna()].index
        entries = list(df.loc[valid, ["row", "pred_bay", "id"]].to_records(index=False))
        self.db.add_images_to_bays(args.vineyard, args.block, "true", "true", entries)

        # Save and return
        df.to_csv(label_file, index=False)
        return df

    def add_image_bytes(self, f_org, args, df=None, batch_size=64):
        # Open the current csv
        label_file = f_org.get_label_file(args.vineyard, args.block, args.date)
        if df is None:
            df = pd.read_csv(label_file, index_col=False)

        def loader(image_path):
            with open(image_path, "rb") as f:
                return f.read()

        # Stride through the dataframe
        for _, chunk in df.groupby(np.arange(len(df)) // batch_size):
            # Get the file names
            if "raw_dir" in chunk.columns:
                file_names = chunk["raw_dir"]
            else:
                image_path = f_org.get_image_path(args.vineyard, args.block, args.date)
                file_names = chunk["name"].apply(lambda x: os.path.join(image_path, x))

            # Load the files in the chunk
            chunk["binary"] = [loader(x) for x in file_names]
            entries = list(chunk[["image_id", "binary"]].to_records(index=False))

            # Store the binaries
            db.add_image_encodings("jpg", entries)

        # Save and return
        df.to_csv(label_file, index=False)
        return df

