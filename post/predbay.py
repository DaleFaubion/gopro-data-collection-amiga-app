
"""
Predicts the row/bay of the image based on the cronology and the predicted
posts
"""

from argparse import ArgumentParser
from os import walk
from os.path import join, getmtime
from collections import namedtuple
from csv import reader, writer
from itertools import cycle, repeat, chain, groupby

ImageInfo = namedtuple("ImageInfo", ["filename", "time"])

LabeledImage = namedtuple("LabelImage", ["filename", "row", "bay"])

MAX_BAY = 21
MIN_BAY = 1
MIN_ROW = 1
MAX_ROW = 21

def main(post_csv, image_dir, out_path):
	"""
	Predicts the rows/bays of the images based onthe cronology and the
	existence of posts
	"""

	# read the post csv and build a map of file -> has post
	posts = read_post_info(post_csv)

	# read the chronology from the FS
	image_info = find_images(image_dir)

	# predict the row/bay based off the order and the posts
	preds = predict_row_bay(posts, image_info)

	# write the row and bays to a CSV file
	write_row_bay(out_path, preds)

	# display a summary of the results
	show_summary(preds)


def predict_row_bay(post_map, image_info):
	"""
	Predicts the row/bay based on the posts and the image info (time),
	assume the image info is already sorted
	"""
	row = 1
	bay = MIN_BAY
	results = []

	#ugly, but python. repeat the row "bays" number of times
	rows = chain.from_iterable([ list(repeat(row, MAX_BAY)) for row in range(MIN_ROW, MAX_ROW +1) ])

	#go up, then down forever
	bays = cycle( list(range(MIN_BAY, MAX_BAY+1)) + list(range(MAX_BAY, MIN_BAY -1, -1)) )

	pred = zip(rows, bays)

	# for each image predict its row/bay
	for i, image in enumerate(image_info):

		if i > 0:
			prev = image_info[i -1]	
			
			if post_map[prev.filename] and not post_map[image.filename]:
				row, bay = next(pred)

		# predict a row/bay image
		image = LabeledImage(image.filename, row, bay)

		results.append(image)


	return results


def read_post_info(post_csv):
	"""
	Reads the post info CSV file, returns a dictionary of filename mapped
	to boolean (post/no post)
	"""
	results = {}

	with open(post_csv) as posts:

		for row in reader(posts):

			filename, raw_post = row

			results[filename] = bool(raw_post)
	
	return results


def write_row_bay(out_path, row_bay_pred):
	"""
	Write the row/bay pred to a CSV file
	"""
	with open(out_path, "w") as csv_file:

		csv_out = writer(csv_file)

		# for each image, write out the predicted row/bay
		for image in row_bay_pred:

			csv_out.writerow([image.filename, image.row, image.bay])


def find_images(image_dir):
	"""
	Returns all the image files in order according to time
	"""
	results = []
	
	# find all the files in the directory and sub-directories
	for root, _, files in walk(image_dir):

		images = [f for f in files if f.lower().endswith("jpg")]

		# load the EXIF data from each image
		for image_file in images:
	
			full_path = join(root, image_file)
			timestamp = getmtime(full_path)
	
			results.append(ImageInfo(full_path, timestamp))


	# sort the image files based on their time
	results = sorted(results, key=lambda f: f.time)

	return results


def show_summary(row_bay_pred):
	"""
	Prints row/bay summaries of the predictions
	"""

	# for each row, print all the bays
	for row, bays in groupby(row_bay_pred):

		print("Row", row)

		# for each bay, print the number of images
		for bay, images in groupby(bays):

			print("Bay", bay, "number of images", len(images))


if __name__ == "__main__":

	parser = ArgumentParser()

	parser.add_argument("posts_csv", help="The CSV file with post predictions")
	parser.add_argument("image_dir", help="The directory with the image files")
	parser.add_argument("out_file", help="The output file")

	args = parser.parse_args()

	main(args.posts_csv, args.image_dir, args.out_file)
