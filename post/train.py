
from argparse import ArgumentParser
from collections import namedtuple, Counter
from random import seed, shuffle
from csv import reader

from PIL import Image
import torch as t
import numpy as np
from torchvision.transforms import Resize

from postmodel import Mk5
from quant import make_predictions, overall_f1, class_f1_scores, NAMES, ibatch

Options = namedtuple("Options", ["hidden", "batch_size", "epochs", "min_epochs", 
	"learning_rate", "reg", "seed", "model_file"])

TRAIN_PROP = .70
DEV_PROP = .1 / (1.0 - TRAIN_PROP)


def main(anno_file_path, options):
	"""
	Trains model to tag images to have a post that marks the end of a bay 
	"""
	t.manual_seed(options.seed)
	seed(options.seed)

	print("Loading Data")

	# load the data
	training, dev, test = load_datasets(anno_file_path, options.batch_size)

	print("Training %d, Dev %d, Testing %d" % (len(training), len(dev), len(test)))

	print("Training", training.counts(), sep="\n")
	print("Dev", dev.counts(), sep="\n")
	print("Testing", test.counts(), sep="\n")

	model = Mk5(options.hidden)

	print("Training Model")
	print("Number of parameters", model.num_parameters())

	model = model.cuda()

	# train the model
	model = model.fit(training, dev, options.epochs, \
		options.learning_rate, options.reg, options.model_file)

	# evaluate the model
	evaluate_model("Training", model, training, options.batch_size)
	evaluate_model("Dev", model, dev, options.batch_size)
	evaluate_model("Testing", model, test, options.batch_size)


def load_datasets(filename, batch_size):
	"""
	Loads the training, dev, testing dataset from the CSV
	"""
	data = []
	
	# load the CSV file, read each line
	with open(filename) as handle:
		
		csv_file = reader(handle)

		for row in csv_file:
			image_file, has_post = row
			data.append( (image_file, int(has_post)) )

	# shuffle the data
	shuffle(data)

	# split the data into train-dev-test split
	training, rest = split_data(data, TRAIN_PROP)
	dev, test = split_data(rest, DEV_PROP)

	return Dataset(training, batch_size), Dataset(dev, batch_size), Dataset(test, batch_size)


class Dataset:
	"""
	A class to lazily load the data from the filesystem
	"""

	def __init__(self, data, batch_size):
		"""
		Initialize the dataset from the csv file
		"""
		self.annos = data
		self.batch_size = batch_size
		self.resize = Resize([300, 400], antialias=True)


	def load_data(self):
		"""
		Lazily loads the images from the FS
		"""
		for image_files, has_posts in ibatch(self.annos, self.batch_size):
	
			# open the file
			images = [self.resize(np.array(Image.open(image_file))) for image_file in image_files]

			# convert the image into a tensor
			x_tensor = t.tensor(images, dtype=t.float).permute(0, 3, 1, 2)

			# convert the response into a tensor
			y_tensor = t.tensor(has_posts, dtype=t.long)

			# yeild the pair
			yield x_tensor, y_tensor


	def shuffle(self):
		shuffle(self.annos)

	def __iter__(self):
		return self.load_data()

	def __len__(self):
		return len(self.annos)

	def counts(self):
		counts = Counter([l for _,l in self.annos])

		names = ["Class %d: %d" % (l,c) for l,c in counts.items()]

		return "\n".join(names)

def split_data(data, prop):
	"""
	Splits the data based on the given proportion
	"""
	point = round(len(data) * prop)

	left = data[:point]
	right = data[point:]

	return left, right


def evaluate_model(group_name, model, dataset):
	"""
	Evaluates the model and prints the results
	"""
	# makes predictions on the dataset
	predictions = make_predictions(model, dataset)

	print("---%s Results---" % group_name)

	# calcuate the f1 scores and print them
	for group, f1_score in enumerate(class_f1_scores(predictions, dataset)):
		
		print("%s F1: %.4f" % (NAMES[group], f1_score))

	# print the f1 scores
	print("Overall F1: %.4f" % overall_f1(predictions, dataset))


if __name__ == "__main__":


	parser = ArgumentParser()

	parser.add_argument("annotation_file", \
		help="The file with the post annotations")

	parser.add_argument("-batch_size", type=int, default=10, \
		help="The batch size")

	parser.add_argument("-hidden", type=int, default=16, \
		help="The size of the NN hidden layers")
	
	parser.add_argument("-learning_rate", type=float, default=.0005, \
		help="The learning rate used to train the model")

	parser.add_argument("-regularizer", type=float, default=.00001, \
		help="The learning rate used to train the model")

	parser.add_argument("-epochs", type=int, default=100, \
		help="Training epochs")
	
	parser.add_argument("-min_epochs", type=int, default=20, \
		help="Training epochs")

	parser.add_argument("-seed", type=int, default=42, \
		help="Random seed")


	parser.add_argument("-o", default="best_model", help="The name of the model file")

	args = parser.parse_args()

	opts = Options(args.hidden, args.batch_size, args.epochs, args.min_epochs, \
		args.learning_rate, args.regularizer, args.seed, args.o + ".p")

	main(args.annotation_file, opts)
