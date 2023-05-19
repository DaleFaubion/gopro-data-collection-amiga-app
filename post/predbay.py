
"""
Predicts the row/bay of the image based on the cronology and the predicted
posts
"""

from argparse import ArgumentParser
from os import walk
from os.path import join, getmtime
from collections import namedtuple
from collections.abc import Iterable
from csv import reader, writer
from itertools import cycle, repeat, chain, groupby
from re import match
from math import log, inf

ImageInfo = namedtuple("ImageInfo", ["filename", "time"])

LabeledImage = namedtuple("LabeledImage", ["filename", "row", "bay"])

HMM = namedtuple("HMM", ["min_pics", "pic_prob", "lag", "post_prob"])
State = namedtuple("State", ["row", "bay", "count"])

MAX_BAY = 21
MIN_BAY = 1
MIN_ROW = 1
MAX_ROW = 100 #TODO change this hack...

def main(post_csv: str, image_dir: str, out_path: str):
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


def predict_row_bay(post_map: dict[str, bool], image_info: list[ImageInfo]) -> list[LabeledImage]:
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

			if post_map[trim_path(prev.filename)] and not post_map[trim_path(image.filename)]:
				row, bay = next(pred)

		# predict a row/bay image
		labeledImage = LabeledImage(image.filename, row, bay)

		results.append(labeledImage)


	return results


def vierbi_path(image_info: list[ImageInfo], params: HMM) -> list[State]:
	"""
	Finds the most likely row/bay assignment to the images based on the 
	sequence of observations of images with or without a post
	"""
	last_t = len(image_info) + 1

	path = []

	# start at row 1, bay 1 the pictures were always taken in that order
	state = State(1, 1, 0)

	# record the probability of being in a state at a given time
	# time -> state -> prob
	probs = {0 : {state : (log(1.0), state)}}

	# for each image (timestep), compute the probably of being in a
	# state (row/bay/pic count)
	for t in range(1, len(image_info) + 1):

		obs = image_info[t - 1]
		probs[t] = {}

		# for each new state (row/bay/count) compute the probability of being
		# in the that state
		for next_st in chain.from_iterable([next_states(p, params) for p in probs[t - 1]]):

			transitions = []
			
			# find the most likely state previous state
			for prev in probs[t - 1]:

				# compute the probability of being in the state, having transitioned
				# from a previous state, and make the current observation
				prob = log(trans_prob(prev, next_st, params)) + \
							log(obs_prob(next_st, obs, params)) + \
							probs[t - 1].get(prev, (-inf, None))[0]
			
				# add the transition/prob
				transitions.append( (prob, prev) )

			# find the best transition
			probs[t][next_st] = max(transitions)

	# find the most likely state to end in
	_, last = max((p, s) for s, (p, _) in probs[last_t].items())

	path.append(last)
	current = last

	# find the Viterbi path, starting with the end (last state) and working
	# backwards in time to the beginning i.e. rewind
	for t in range(last_t, 0, -1):
		_, current = probs[t][current]
		path.append(current)

	return list(reversed(path))


def next_states(state: State, params: HMM) -> list[State]:
	"""
	Generates the non-zero probability successor states
	"""
	# the bays increase on odd rows and decrease on even
	goingUp = state.count % 2 == 1
	inc = 1 if goingUp else -1
	nextCount = state._replace(count = state.count + 1)
	nextBay = state._replace(bay = state.bay + 1, count = 1)
	
	if state.count < params.min_pics:

		return [nextCount]

	# if the bays are going up and at the end
	# of if bays are going down and at the end
	elif (goingUp and state.bay == MAX_BAY) or (not goingUp and state.bay == MIN_BAY):
	
		return [nextCount, state._replace(row = state.row + 1, count = 1)]

	# else move to the next bay/count
	else:
	
		return [nextCount, nextBay]


def trans_prob(prev, current, params):
	"""
	Specifies the transition probability from the previous state to the given
	state
	"""
	# probability of increment pic count is geometric past a point, below 
	# the cut-off it is simply 1
	# the probability of the moving to the next row/bay is 1 - increment prob
	
	# the probability of incrementing the picture is simply picture prob.
	if prev.bay == current.bay and prev.row == current.row:
		prob = params.pic_prob

	# the probability of moving to a new bay is 1 - picture prob
	else:
		prob = 1.0 - params.pic_prob
		
	return prob


def obs_prob(state, obs, params):
	"""
	Specifies the probability of observing a post in the given state
	"""
	# high probability around the beginning or end

	# expected picture count: constant plus expected count of geometric dist
	expected = params.min_pic + (1 / params.pic_prob)

	# the probability of observing
	if state.count >= expected or state.count <= params.lag:
		prob = params.post_prob
	
	else:
		prob = 1.0 - params.post_prob

	return prob


def read_post_info(post_csv: str) -> dict[str,bool]:
	"""
	Reads the post info CSV file, returns a dictionary of filename mapped
	to boolean (post/no post)
	"""
	results = {}

	with open(post_csv) as posts:

		for row in reader(posts):

			filename, raw_post = row
			results[trim_path(filename)] = bool(int(raw_post))
	
	return results


def write_row_bay(out_path: str, row_bay_pred: list[LabeledImage]) -> None:
	"""
	Write the row/bay pred to a CSV file
	"""
	with open(out_path, "w") as csv_file:

		csv_out = writer(csv_file)

		# for each image, write out the predicted row/bay
		for image in row_bay_pred:

			csv_out.writerow([image.filename, image.row, image.bay])


def find_images(image_dir: str) -> list[ImageInfo]:
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


def trim_path(path: str) -> str:
	"""
	Trims the path, removes everything before the date
	"""
	i = 0
	found = False

	parts = path.split("/")

	# find the date part of the path
	while i < len(path) and not found:
	
		if match(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", parts[i]):
			found = True

		else:
			i += 1

	return join(*parts[i:])


def show_summary(row_bay_pred: list[LabeledImage]) -> None:
	"""
	Prints row/bay summaries of the predictions
	"""

	# for each row, print all the bays
	for row, bays in groupby(row_bay_pred, key=lambda r: r.row):

		print("Row", row)

		# for each bay, print the number of images
		for bay, images in groupby(bays, key=lambda b: b.bay):

			print("Bay", bay, "number of images", len(list(images)))


if __name__ == "__main__":

	parser = ArgumentParser()

	parser.add_argument("posts_csv", help="The CSV file with post predictions")
	parser.add_argument("image_dir", help="The directory with the image files")
	parser.add_argument("out_file", help="The output file")

	args = parser.parse_args()

	main(args.posts_csv, args.image_dir, args.out_file)
