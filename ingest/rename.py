
"""
A module to 'rename' the image file names in the locations CSV file
"""

from os.path import realpath

import pandas as pd

from common import COLUMNS

def rename(f_org, vineyard, block, date, df=None):
	"""
	main adds the relative path to the image from images directory.
	"""

	# Open the current csv
	label_file = f_org.get_label_file(vineyard, block, date)
	
	if df is None:
		df = pd.read_csv(label_file, index_col=False)

	print("Renaming column instead of moving files for now")

	# parse the filename out of the 
	df["name"] = df["raw_dir"].apply(
		lambda x: x[x.find(date) + len(date) + 1 :]
	)

	# rename the path
	df["raw_dir"] = df["raw_dir"].apply(realpath)

	#write the changes to file
	df[COLUMNS].to_csv(label_file)

	return df[COLUMNS]
