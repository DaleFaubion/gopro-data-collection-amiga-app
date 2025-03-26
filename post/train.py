
from argparse import ArgumentParser
from collections import namedtuple, Counter
from random import seed, shuffle, uniform
from csv import reader

from PIL import Image
import torch as t
import numpy as np
from torchvision import transforms as tt
from torchvision.transforms import functional as tf

from postmodel import Mk5, VGG16, ResNet18
from quant import make_predictions, overall_f1, class_f1_scores, NAMES, ibatch, write_errors, calc_class_weights, NO_POST, HAS_POST

Options = namedtuple("Options", ["hidden", "batch_size", "epochs", "min_epochs", 
	"learning_rate", "reg", "seed", "model_file", "use_vgg", "use_res18"])

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

	class_weight = calc_class_weights(len(training) - training.num_posts(), training.num_posts())

	if options.use_vgg:
		print("Using VGG")
		model = VGG16(options.hidden, class_weight)
	elif options.use_res18:
		print("Using ResNet-18")
		model = ResNet18()
	else:
		print("Using LeNet")
		model = Mk5(options.hidden)

	print("Training Model")
	print("Number of parameters", model.num_parameters())

	model = model.cuda()

	# train the model
	model = model.fit(training, dev, options.epochs, \
		options.learning_rate, options.reg, options.model_file)

	# evaluate the model
	evaluate_model("Training", model, training)
	evaluate_model("Dev", model, dev)
	evaluate_model("Testing", model, test, True)


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
	#shuffle(data)

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
		self.batch_size = batch_size
		self.annos = [(self.load_image(i), l) for i,l in data]
		self.names = data
		self.aug = tt.Compose([
								 #tt.RandomRotation(10),
								 tt.RandomHorizontalFlip(),
								 #tt.RandomPerspective(.1)  #causes warning
								 #tt.ColorJitter(brightness=0.5),
                                 #tt.RandomAffine(0, scale=(.8, 1.2))
								 #tt.GaussianBlur((5,5), (0.001, .5))
								])

	
	def load_image(self, img_path):

		# open the image file
		img = Image.open(img_path)

		return img.resize((800, 600))


	def augment_data(self, img):
		
		img = self.aug(img)
		
		# sample a random brightness factor
		brightness = uniform(.5, 1.75)

		return tf.adjust_brightness(img, brightness)
		#return img


	def load_data(self, augment=False):
		"""
		Lazily loads the images from the FS
		"""
		for images, has_posts in ibatch(self.annos, self.batch_size):

			# augment the data by applying random transformations
			if augment:
				images = [self.augment_data(img) for img in images]

			# convert the images into a tensor
			x_tensor = t.stack([self.to_tensor(img) for img in images], 0)

			# convert the response into a tensor
			y_tensor = t.tensor(has_posts, dtype=t.long)

			# yeild the pair
			yield x_tensor, y_tensor


	def to_tensor(self, pil_img):
		"""
		Returns the image as a tensor
		"""
		# make into a tensor and put the channels in font to match
		# pytorch's convention (resize and cnn)
		return t.tensor(np.array(pil_img), dtype=t.float).permute(2, 0, 1)

	def no_aug_iter(self):
		return self.load_data(False)

	def flat_iter(self):
		return self.annos

	def aug_iter(self):
		return self.load_data(True)

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

	def num_posts(self):
		return sum( int(l == HAS_POST) for _, l in self.annos )

def split_data(data, prop):
	"""
	Splits the data based on the given proportion
	"""
	point = round(len(data) * prop)

	left = data[:point]
	right = data[point:]

	return left, right


def evaluate_model(group_name, model, dataset, write_errs=False):
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

	if write_errs:
		write_errors("%s_errors.txt" % group_name, predictions, dataset)


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

	parser.add_argument("-vgg16", action="store_true", help="Use a VGG-16 model")

	parser.add_argument("-res18", action="store_true", help="Use a ResNet-18 model")

	parser.add_argument("-o", default="best_model", help="The name of the model file")

	args = parser.parse_args()

	opts = Options(args.hidden, args.batch_size, args.epochs, args.min_epochs, \
		args.learning_rate, args.regularizer, args.seed, args.o + ".p", args.vgg16, args.res18)

	main(args.annotation_file, opts)
