
"""
A module to 'rename' the image file names in the locations CSV file
"""

from os.path import realpath

from ingest.common import COLUMNS

def rename(data, date, image_dir):
	"""
	main adds the relative path to the image from images directory.
	"""

	print("Renaming column instead of moving files for now")

	# parse the filename out of the 
	data["name"] = data["raw_dir"].apply(
		lambda path: path[path.find(image_dir) + len(image_dir) + 1 :])

	# rename the path
	data["raw_dir"] = data["raw_dir"].apply(realpath)

	return data[COLUMNS]
