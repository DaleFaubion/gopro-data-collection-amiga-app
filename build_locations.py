
"""
Build a locations CSV file - the location of each image along with other
meta-data
"""

import os
from argparse import ArgumentParser

import numpy as np
import pandas as pd

from ingest import gencsv, fix, pred, rename


def main(image_dir, file_path, vineyard, block, date, labeled_data, dry_run):
	"""
	Ingests the images indicated by the passed args object.
	"""
	
	# if the directory contains images, proceed with creating the locations file
	if len(os.listdir(image_dir)):

		# load the labled data
		labeled = load_labeled_data(labeled_data)

		print("Creating the CSV")
		data = gencsv.create_csv(vineyard, block, date, image_dir)

		#TODO remove
		data.to_csv("pre_fix.csv")

		print("Fill in the missing GPS data")
		data = fix.predict(data)

		#TODO remove
		data.to_csv("post_fix.csv")
		
		if not dry_run:
			
			print("Predicting the row")
			data = pred.predict(data, labeled, "row")

			print("Predicting the bay")
			data = pred.predict(data, labeled, "bay")

			print("Renaming")
			data = rename.rename(data, date)

			# write out the CSV file
			data.to_csv(file_path)
		
	else:
		print("Chosen path does not contain files")
		print("Make sure to run setup.sh from the root repo")


def load_labeled_data(label_file):
	"""
	Loads the labled data - just the locations file with the row/bay
	meta-data
	"""
	training = pd.read_csv(label_file, index_col=False)
	#training = training[training["bay"].notna()]
	#training = training[np.logical_and(training["row"].notna(), training["bay"].notna())]
	
	return training


if __name__ == "__main__":
	
	ap = ArgumentParser()

	ap.add_argument("-i", "--image_dir", required=True, help="The directory of images")
	ap.add_argument("-d", "--date", required=True, help="date to ingest (yyyy-mm-dd)")
	ap.add_argument("-l", "--labeled_data", required=True, help="The locations file labeled row and bay")
	
	ap.add_argument("-f", "--file_path", default="locations.csv", help="The path of the CSV file to create")
	ap.add_argument("-v", "--vineyard", default="crawford-beck", help="vineyard name")
	ap.add_argument("-b", "--block", default=9, type=int, help="block number")

	ap.add_argument("-s", "--dry_run", action="store_true", help="Do not save the results")

	args = ap.parse_args()

	main(**vars(args))
