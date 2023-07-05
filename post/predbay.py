
"""
A module that predicts the bay of an image given when it was taken and
its previously predicted row
"""

from argparse import ArgumentParser
from csv import reader, writer
from collections import namedtuple
from itertools import groupby

from os.path import basename

from hmmlearn.hmm import CategoricalHMM
import numpy as np

NUM_BAYS = 21
STATES_PER_BAY = 3
NUM_STATES = NUM_BAYS * STATES_PER_BAY

STATES_PER_BAY_2021 = 2
NUM_STATES_2021 = NUM_BAYS * STATES_PER_BAY_2021

ImageData = namedtuple("ImageData", ["file", "date", "time", "row", "post", "bay"])


def main(row_file, post_file, out_file, mid_size, end_size, is_2021):
	"""
	Predicts the bay for each image in the CSV file
	"""
	# create an HMM
	if is_2021:
		hmm = create_hmm_2021(mid_size, end_size)
		states_per_bay = STATES_PER_BAY_2021
	else:
		hmm = create_hmm(mid_size, end_size)
		states_per_bay = STATES_PER_BAY

	# load the data
	# predict bays
	# write back to file
	write_data(out_file, predict_bays(hmm, load_data(row_file, post_file), states_per_bay))


def create_hmm(images_per_bay: float, bookend_size: float) -> CategoricalHMM:
	"""
	Creates an HMM model to predict the bay
	"""
	hmm = CategoricalHMM(n_components=NUM_STATES)

	# only start in the first state
	start_probabilities = np.array([1.0] + ([0.0] * (NUM_STATES -1)) )

	# only see posts in the "bookends"
	emission_probabilities = np.array([
						[0.01, 0.99],
						[0.99, 0.01],
						[0.01, 0.99],
					] * NUM_BAYS)

	transition_probabilities = make_trans_matrix(images_per_bay, bookend_size)

	hmm.startprob_ = start_probabilities
	hmm.transmat_ = transition_probabilities
	hmm.emissionprob_ = emission_probabilities
	
	return hmm


def create_hmm_2021(images_per_bay: float, bookend_size: float) -> CategoricalHMM:
	"""
	Creates a "shorter" HMM for the year 2021
	"""
	hmm = CategoricalHMM(n_components=NUM_STATES_2021)

	# only start in the first state
	start_probabilities = np.array([1.0] + ([0.0] * (NUM_STATES_2021 -1)) )

	# only see posts in the "bookends"
	emission_probabilities = np.array([
						[0.01, 0.99],
						[0.99, 0.01],
					] * NUM_BAYS)

	transition_probabilities = make_trans_matrix_2021(images_per_bay, bookend_size)

	hmm.startprob_ = start_probabilities
	hmm.transmat_ = transition_probabilities
	hmm.emissionprob_ = emission_probabilities
	
	return hmm

def make_trans_matrix(images_per_bay: int, bookend_size: int) -> np.array:
	"""
	Builds the transition matrix based on the number of images per bay
	"""
	EPS = 0.0001
	trans_matrix = np.zeros( (NUM_STATES, NUM_STATES) )

	# transition prob, geometric dist
	mid_leave_prob = (1.0 / images_per_bay) - EPS

	# assumes symmetry of "bookend"
	end_leave_prob = (1.0 / bookend_size) - EPS

	probs_template = [end_leave_prob, mid_leave_prob, end_leave_prob]

	# print out the row/bay information
	# fill out a diagonal of the transition matrix
	# i.e. transitions between states within a bay and to the next bay
	for bay in range(0, NUM_STATES, STATES_PER_BAY):

		for leave_prob, state in zip(probs_template, range(bay, bay + STATES_PER_BAY + 1)):
		
			# check if there is a next state
			if state + 1 < NUM_STATES:
				trans_matrix[state][state + 1] = leave_prob
				trans_matrix[state][state] = 1.0 - leave_prob

			# else just stay in the last state
			else:
				trans_matrix[state][state] = 1.0


	return trans_matrix


def make_trans_matrix_2021(images_per_bay: float, bookend_size: float) -> np.array:
	"""
	Builds the transition matrix based on the number of images per bay
	"""
	EPS = 0.0001
	trans_matrix = np.zeros( (NUM_STATES_2021, NUM_STATES_2021) )

	# transition prob, geometric dist
	mid_leave_prob = (1.0 / images_per_bay) - EPS

	# assumes symmetry of "bookend"
	end_leave_prob = (1.0 / bookend_size) - EPS

	probs_template = [end_leave_prob, mid_leave_prob]

	# print out the row/bay information
	# fill out a diagonal of the transition matrix
	# i.e. transitions between states within a bay and to the next bay
	for bay in range(0, NUM_STATES_2021, STATES_PER_BAY_2021):

		for leave_prob, state in zip(probs_template, range(bay, bay + STATES_PER_BAY_2021 + 1)):
		
			# check if there is a next state
			if state + 1 < NUM_STATES_2021:
				trans_matrix[state][state + 1] = leave_prob
				trans_matrix[state][state] = 1.0 - leave_prob

			# else just stay in the last state
			else:
				trans_matrix[state][state] = 1.0


	return trans_matrix


def predict_bays(hmm: CategoricalHMM, img_data: list[ImageData], states_per_bay: int) -> list[ImageData]:
	"""
	Predicts the bay for each image
	"""
	results = []
	bay_count = {}

	# group up the images into chunks based on rows
	# for each row, predict the bays for each image
	for row_num, row in groupby(img_data, key=lambda i: i.row):

		row = list(row)

		# make the row into a numpy array
		row_array = np.array([i.post for i in row])

		#make the array 2D
		row_array = row_array.reshape(1, -1)

		# use the HMM to predict bays
		_, seq = hmm.decode(row_array, algorithm="viterbi")

		# update the image data
		for img, state in zip(row, seq):

			bay = (state // states_per_bay) + 1

			bay_count[(row_num, bay)] = bay_count.get((row_num, bay), 0) + 1

			# even rows were traversed in reverse order
			if row_num % 2 == 0:
				bay = NUM_BAYS - bay + 1

			# adjust down from multiple states per bay down to bay number
			img = img._replace(bay = bay)
			results.append(img)


	# print out the row/bay information
	for (row, bay), count in bay_count.items():
		print("Row %2d Bay %2d: %3d" % (row, bay, count))

	return results


def load_data(row_file: str, post_file: str) -> list[ImageData]:
	"""
	Loads the image data from the CSV file
	"""
	results = []
	post_pred = {}
	
	with open(post_file) as post_in:
		for row in reader(post_in):
			file, post = row
			post_pred[basename(file)] = int(post)


	with open(row_file) as in_file:
		for row in reader(in_file):
			file, date, time, row_id = row
			results.append(ImageData(file, date, time, int(row_id), post_pred[basename(file)], None))

	return results


def write_data(csv_out: str, image_data: list[ImageData]):
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
	parser.add_argument("-m", default=5.0, type=float, 
		help="Expected number of images in the middle of a bay")
	parser.add_argument("-e", default=1.0, type=float, 
		help="Expected number of images on one end of a bay (two ends)")
	parser.add_argument("-y", action="store_true", 
		help="Use the 2021 HMM which has fewer states")

	args = parser.parse_args()


	main(args.row_csv, args.post_csv, args.out_csv, args.m, args.e, args.y)
