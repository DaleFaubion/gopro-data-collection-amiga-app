"""
Ingest images along with meta-data into the database

Uses the 'locations.csv' file to determine what to ingest
"""

from argparse import ArgumentParser

import pandas as pd
from PIL import Image

import database as d
from ingest.ingestdb import Ingester

# the id for East
EAST = 0

def main(bay_file, harvest_file, db_conf, vineyard, block, year, resize, add_orientation):
	"""
	Ingests the images indicated by the passed args object.
	"""
	# load the image location data
	images = pd.read_csv(bay_file)

	columns = ["file_name", "date", "time", "row", "bay"]

	# add the missing columns names
	if add_orientation:
		images.columns = columns
		images["orient_id"] = [EAST] * len(images)

	else:
		columns += ["orient_id"]
		images.columns = columns

	# load the harvest data
	harvest = pd.read_csv(harvest_file)

    # remove rows/bays that don't exist
	images = images[ (images.row >= 1) & (images.row <= 21) & (images.bay >= 1) & (images.bay <= 21) ]

	# Connect to the database
	db_conn = d.Database()
	db_conn.connect(db_conf)

	# Ensure the schema is up to date
	# db.create_schema(Schema)
	db_loader = Ingester(db_conn)

	# add a UUID to the images
	db_loader.add_uuids(images)

	# add the image meta-data
	db_loader.add_metadata(images)

	# add image info to each bay
	db_loader.add_images_to_bays(images, vineyard, block)

	# add image binaries
	db_loader.add_image_bytes(images, resize_dims=resize)

	# add harvest (yield weight) data
	db_loader.add_harvest_data(harvest, vineyard, block, year)


if __name__ == "__main__":

	ap = ArgumentParser()

	ap.add_argument("harvest_file", help="The CSV file with harvest weights")
	ap.add_argument("bay_file", help="The predicted row/bay CSV file with image meta-data")
	ap.add_argument("-v", "--vineyard", default="crawford-beck", help="vineyard name")
	ap.add_argument("-b", "--block", default=9, type=int, help="block number")
	ap.add_argument("-y", "--year", required=True, help="the harvest year to ingest (yyyy)")
	ap.add_argument("-db", "--db_conf", default="db.conf", help="Database config files")
	ap.add_argument("-resize", "--resize", nargs=2, default=[], required=False, type=int, 
		help="The W,H dimensions of the resized image that will be loaded into the database")
	ap.add_argument("-o", "--add-orientation", action="store_true", 
		help="Defaults to an Eastward orientation")

	args = ap.parse_args()

	# Convert to tuple
	if len(args.resize) != 2:
		args.resize = None
		print("Using default resolution of images for ingest")
	else:
		args.resize = tuple(args.resize)
		print(f"Dimensions to resize images: {args.resize[0]}x{args.resize[1]}")

	main(**vars(args))
