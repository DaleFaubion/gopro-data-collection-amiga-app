"""
A script to find and count the number of images with 
corrupted GPS
"""

from os import walk
from os.path import join
from argparse import ArgumentParser
from collections import namedtuple

import numpy as np
from PIL import Image, UnidentifiedImageError

from ingest.gencsv import parse_gps

ImageFile = namedtuple("ImageFile", ["filename", "corrupted"])

CorruptStats = namedtuple("CorruptStats", ["num_good", "num_corrupt"])


def count_corrupt(image_path, out_file, extension):
	"""
	Counts up the images with corrupt GPS data and
	writes them to a file
	"""
	with open(out_file, "w") as out:

		# collect the names of the files with/without corrupt GPS
		image_files = collect_images(image_path, extension)

		# generate stats on corrupt vs intact data
		stats = calc_stats(image_files)

		# print stats
		print("\nGood files %d\nCorrupt files %d\nTotal files %d" \
			% (stats.num_good, stats.num_corrupt, stats.num_good + stats.num_corrupt))

		# write stats
		write_statistics(out, stats)

		# write corrupt file names
		write_corrupt_names(out, image_files)


def collect_images(image_dir, extension):
	"""
	Collects the names of all the image files and
	mark them as corrupt or valid
	"""
	results = []

	# walk the directory and collect image files
	for root, _, files in walk(image_dir):

		for img_file in files:

			# only count the image files
			if img_file.lower().endswith(extension):
				
				# complete the file path
				full_path = join(root, img_file)

				# check the exinf data
				image_file = ImageFile(full_path, is_corrupt(full_path))

				# add the file to the results
				results.append(image_file)

				if len(results) % 100 == 0:
					print("\rProcessed %d" % len(results), end="")


	return results


def calc_stats(image_files):
	"""
	Counts up some statistics on the image files
	"""
	good = 0
	corrupt = 0
	
	# count up all the corrupt files
	for img_file in image_files:
		
		if img_file.corrupted:
			corrupt += 1
		else:
			good += 1

	return CorruptStats(good, corrupt)


def is_corrupt(filename):
	"""
	Returns true if the image file has corrupt GPS data
	"""
	corrupted = True

	try:

		with Image.open(filename) as img:

			#get all the exif info
			info = img._getexif()
			
			lat, lon = parse_gps(info)

			corrupted = (np.isnan(lat) or np.isnan(lon))
	
	except UnidentifiedImageError:
		# there is an error opening the file
		pass

	return corrupted


def write_statistics(out_file, statistics):
	"""
	Write the statistics to the file
	"""
	out_file.write("Good Files: %s\n" % statistics.num_good)
	out_file.write("Corrupt Files: %s\n" % statistics.num_corrupt)
	out_file.write("Total Files: %s\n\n" % (statistics.num_good + statistics.num_corrupt))


def write_corrupt_names(out_file, image_files):
	"""
	Write the names of the corrupt image files
	"""
	# write out all the corrupt files
	for img_file in image_files:
		if img_file.corrupted:
			out_file.write("%s\n" % img_file.filename)


def main():
	"""
	Traverses a directory, counting the number of image
	files with corrupt GPS data
	"""
	parser = ArgumentParser()

	parser.add_argument("image_path", help="The path that contains all the image files")
	
	parser.add_argument("-o", "--out_file", default="corrupt_files.txt", \
		help="The file to write the stats/corrupt files to")
	
	parser.add_argument("-e", "--extension", default="jpg", help="The file extension of images")

	args = parser.parse_args()

	count_corrupt(**vars(args))

if __name__ == "__main__":
	main()
