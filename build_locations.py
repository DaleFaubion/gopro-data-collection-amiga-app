
"""
Build a locations CSV file - the location of each image along with other
meta-data
"""

import os
from os.path import join
from argparse import ArgumentParser

import numpy as np
import pandas as pd

from ingest import gencsv, fix, pred, rename, rowpred, angle

LOC = "locations.csv"

def main(image_dir, out_dir, vineyard, block, date, num_rows, labeled_data):
	"""
	Ingests the images indicated by the passed args object.
	"""
	out_file = join(out_dir, LOC)
	
	# if the directory contains images, proceed with creating the locations file
	if len(os.listdir(image_dir)):

		# load the labled data
		labeled = load_labeled_data(labeled_data)

		print("Creating the CSV")
		data = gencsv.create_csv(vineyard, block, date, image_dir)

		print("Fill in the missing GPS data")
		data = fix.predict(data, out_dir)

		print("Predicting the row")
		data = rowpred.predict(data, num_rows, out_dir)

		print("Predicting the bay")
		data = pred.predict(data, labeled, "bay", out_dir)

		print("Predict the camera angle")
		data = angle.predict(data)

		print("Renaming")
		data = rename.rename(data, date, image_dir)

		# write out the CSV file
		data.to_csv(out_file)
		
	else:
		print("Chosen path does not contain files")
		print("Make sure to run setup.sh from the root repo")


def load_labeled_data(label_file):
	"""
	Loads the labled data - just the locations file with the row/bay
	meta-data
	"""
	training = pd.read_csv(label_file, index_col=False)
	
	return training


if __name__ == "__main__":
	
	ap = ArgumentParser()

	ap.add_argument("-i", "--image_dir", required=True, help="The directory of images")
	ap.add_argument("-d", "--date", required=True, help="date to ingest (yyyy-mm-dd)")
	ap.add_argument("-l", "--labeled_data", required=True, help="The locations file labeled row and bay")
	
	ap.add_argument("-o", "--out_dir", default=".", help="The path to write the output files to")
	ap.add_argument("-v", "--vineyard", default="crawford-beck", help="vineyard name")
	ap.add_argument("-b", "--block", default=9, type=int, help="block number")
	ap.add_argument("-r", "--num_rows", default=21, type=int, help="The number of rows")

	args = ap.parse_args()

	main(**vars(args))
