
"""
Build a locations CSV file - the location of each image along with other
meta-data
"""

import os
from argparse import ArgumentParser


import file_org as f_org
from ingest import gencsv, fix, rowpred, baypred, rename


def main(vineyard, block, date, rows, raw_dir):
	"""
	main ingests the images indicated by the passed args object.
	"""

	# look up default directory for the images
	if not args.raw_dir:
		args.raw_dir = f_org.get_image_path(vineyard, block, date)

	# if the directory contains images, proceed with creating the locations file
	if len(os.listdir(raw_dir)):
		gencsv.main,

		print("Creating the CSV")
		df = gencsv.create_csv(f_org, vineyard, block, date)

		print("Fill in the missing GPS data")
		df = fix.predict(f_org, vineyard, block, date, rows, df)
		
		print("Predicting the row")
		df = rowpred.predict(f_org, vineyard, block, date, rows, df)

		print("Predicting the bay")
		df = baypred.predict(f_org, vineyard, block, date, df)

		print("Renaming")
		df = rename.rename(f_org, vineyard, block, date, df)
		
	else:
		print("Chosen path does not contain files")
		print("Make sure to run setup.sh from the root repo")


if __name__ == "__main__":
	
	ap = ArgumentParser()

	ap.add_argument("-v", "--vineyard", default="crawford-beck", help="vineyard name")
	ap.add_argument("-b", "--block", default=9, type=int, help="block number")
	ap.add_argument("-d", "--date", required=True, help="date to ingest (yyyy-mm-dd)")

	ap.add_argument("-r", "--rows", default=21, help="number of rows in block")
	ap.add_argument("-raw_dir", help="directory of unprocessed images")

	args = ap.parse_args()

	main(args)
