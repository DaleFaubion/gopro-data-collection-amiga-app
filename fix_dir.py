"""
A program to recreate the nested directories for the 2019 data
"""

from argparse import ArgumentParser
from os.path import join, exists
from os import mkdir, rename

import pandas as pd

def main(location_file, image_dir):
	"""
	Creates subdirectories according the camera angles and moves image files
	accordingly
	"""

	# load the location file
	image_data = pd.read_csv(location_file)

	# get all the camera angles
	angles = [str(a) for a in image_data["angle"].unique()]

	print("All the angles:")
	print("\n".join(angles))

	# create a sub-directory per angle
	for angle in angles:
		new_dir = join(image_dir, angle)

		if not exists(new_dir):
			mkdir(new_dir)

	# for each image, move it based on the camera angle
	for file_name, angle in image_data[ ["name", "angle"] ].to_numpy():

		src_file = join(image_dir, file_name)

		# move the file
		if exists(src_file):
			rename(src_file, join(image_dir, str(angle), file_name))
		else:
			print("%s does not exist" % src_file)


if __name__ == "__main__":

	
	parser = ArgumentParser()
	parser.add_argument("location_file", help="The CSV file with the image information in it")
	parser.add_argument("image_dir", help="The image directory")

	args = parser.parse_args()

	main(args.location_file, args.image_dir)
