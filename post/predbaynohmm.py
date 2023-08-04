
"""
A module that predicts the bay of an image given when it was taken and
its previously predicted row
"""

from argparse import ArgumentParser
from csv import reader, writer
from collections import namedtuple
from itertools import groupby, chain

from os.path import basename, join

from hmmlearn.hmm import CategoricalHMM
import numpy as np


ImageData = namedtuple("ImageData", ["file", "date", "time", "row", "post", "bay"])

Images = list[ImageData]


def main(row_file, post_file, out_file):
	"""
	Predicts the bay for each image in the CSV file
	"""
	# load the data
	# smooth data
	# predict bays
	# write back to file
	write_data(out_file, predict_bays(smooth_pred(load_data(row_file, post_file))))


def smooth_pred(img_data: Images) -> Images:
	"""
	Smooth out the potential false positives in the data
	"""

	# for each entry, if the predicted end post (1) is surrounded by 0's
	# then make the prediction a zero
	for i in range(1, len(img_data) - 1):

		prev = img_data[i - 1].post == 0
		adv = img_data[i + 1].post == 0
		is_end = img_data[i].post == 1

		# make the current prediction "no post"
		if prev and is_end and adv:
			img_data[i] = img_data[i]._replace(post = 0)

	return img_data


def predict_bays(img_data: Images) -> Images:
	"""
	Group up the image data to predict bays
	"""
	bays = []

	# group up the images into chunks based on rows
	# for each row, predict the bays for each image
	for row_num, row_img_data in groupby(img_data, key=lambda i: i.row):

		bay_counts = {}
		bay_num = 1

		# group up the images into rows 
		groups = [list(g) for _, g in groupby(row_img_data, key=lambda r: r.post)]

		# the groups should go posts, no posts, posts, no posts, posts, ...
		# hence every "posts" group needs to be split in half
		split_groups = []	

		for i, group in enumerate(groups):
			
			# even indexed groups will be "posts"
			# skip the first and last "posts" group
			if i > 0 and i < len(groups) -1 and i % 2 == 0:
				mid = len(group) // 2
				first = group[:mid]
				second = group[mid:]
				split_groups.append(first)
				split_groups.append(second)

			else:
				split_groups.append(group)

		for i in range(0, len(split_groups), 3):
			parts = split_groups[i:i + 3]

			for img in chain(*parts):
				new_img = img._replace(bay = bay_num)
				bays.append(new_img)
				bay_counts[bay_num] = bay_counts.get(bay_num, 0) + 1

			bay_num += 1

		# print out information about the rows
		for bay, count in bay_counts.items():
			print("Row %2d Bay %2d: %d" % (row_num, bay, count))

	return bays 


def load_data(row_file: str, post_file: str) -> Images:
	"""
	Loads the image data from the CSV file
	"""
	results = []
	post_pred = {}
	
	with open(post_file) as post_in:
		for row in reader(post_in):
			file, post = row
			post_pred[get_rel_path(file)] = int(post)


	with open(row_file) as in_file:
		for row in reader(in_file):
			file, date, time, row_id = row
			results.append(ImageData(file, date, time, int(row_id), post_pred[get_rel_path(file)], None))


	#TODO remove
	for img in results:
		print("data: %s %d" % (img.file, img.post))

	return results


def get_rel_path(full_path):
	"""
	Standardizes the path by making it relative
	"""
	parts = full_path.split("/")
	index = parts.index("block09") + 1

	return join(*parts[index:])


def write_data(csv_out: str, image_data: Images):
	"""
	Writes out the bay predictions
	"""
	with open(csv_out, "w") as out:
		
		write_out = writer(out)
		
		for img in image_data:
			write_out.writerow([img.file, img.date, img.time, img.row, img.bay])


if __name__ == "__main__":

	parser = ArgumentParser()
	
	parser.add_argument("row_csv", help="Image CSV file with predicted rows")
	parser.add_argument("post_csv", help="Image CSV file with predicted posts")
	parser.add_argument("out_csv", help="The file to write to")

	args = parser.parse_args()


	main(args.row_csv, args.post_csv, args.out_csv)
