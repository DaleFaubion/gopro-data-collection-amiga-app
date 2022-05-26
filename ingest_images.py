"""
Ingest images along with meta-data into the database

Uses the 'locations.csv' file to determine what to ingest
"""

from argparse import ArgumentParser

import pandas as pd
from PIL import Image

import database as d
from ingest.ingestdb import Ingester

def main(location_file, harvest_file, db_conf, image_dir, vineyard, block, date, resize):
	"""
	Ingests the images indicated by the passed args object.
	"""

	# load the image location data
	images = pd.read_csv(location_file)

	# load the harvest data
	harvest = pd.read_csv(harvest_file)

	# Connect to the database
	db_conn = d.Database()
	db_conn.connect(db_conf)

	# Ensure the schema is up to date
	# db.create_schema(Schema)
	db_loader = Ingester(db_conn)

	# add a UUID to the images
	db_loader.add_uuids(images)

	# ingest the bay info
	db_loader.add_bays(images, vineyard, block)

	# add the image meta-data
	db_loader.add_metadata(images)

	# add image info to each bay
	db_loader.add_images_to_bays(images, vineyard, block)

	# add image binaries
	db_loader.add_image_bytes(images, image_dir, resize_dims=resize)

	# add harvest (yield weight) data
	db_loader.add_harvest_data(harvest, vineyard, block, date)


if __name__ == "__main__":

	ap = ArgumentParser()

	ap.add_argument("harvest_file", help="The CSV file with harvest weights")
	ap.add_argument("location_file", help="The location CSV file with image meta-data")
	ap.add_argument("-v", "--vineyard", default="crawford-beck", help="vineyard name")
	ap.add_argument("-b", "--block", default=9, type=int, help="block number")
	ap.add_argument("-d", "--date", required=True, help="date to ingest (yyyy-mm-dd)")
	ap.add_argument("-i", "--image_dir", help="directory of unprocessed images")
	ap.add_argument("-db", "--db_conf", default="db.conf", help="Database config files")
	ap.add_argument("-resize", "--resize", nargs=2, default=[], required=False, type=int, help="The W,H dimensions of the resized image that will be loaded into the database")

	args = ap.parse_args()

	# Convert to tuple
	if len(args.resize) != 2:
		args.resize = None
		print("Using default resolution of images for ingest")
	else:
		args.resize = tuple(args.resize)
		print(f"Dimensions to resize images: {args.resize[0]}x{args.resize[1]}")

	main(**vars(args))
