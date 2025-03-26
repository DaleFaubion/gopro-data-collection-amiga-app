from time import time
from typing import Union
import torch as t
import torch.nn as nn
from torch.optim import SGD
import numpy as np

from quant import make_predictions, overall_f1, class_f1_scores, HAS_POST, NO_POST

RGB=3

class Model(nn.Module):

	def __init__(self):
		super().__init__()
	
	def fit(self, train_data, dev_data, num_epochs, learning_rate, reg, model_path):
		"""
		Trains the model, the data collections are iterables of (inst, target) tuples
		"""
		MIN_ROUND = min(10, num_epochs)
		params = [p for p in self.parameters() if p.requires_grad]
		optim = SGD(params, learning_rate, weight_decay=reg, momentum=0.9)
		best_f1 = 0.0
		best_epoch = 0
		self.train()
		epoch = 1

		# for a fixed number of epochs, train the model
		while epoch <= num_epochs:
			print("Epoch %4d |" % epoch, end="")
			start_time = time()
			total_loss = 0.0
			
			#train_data.shuffle()
			
			# for each training batch, make a prediction, measure the loss, and update
			for inst, target in train_data.aug_iter():
				self.zero_grad()
				pred = self(inst.cuda())

				loss = self.loss_function(pred, target.cuda())
				total_loss += loss.cpu().data.item()
				loss.backward()
				optim.step()
		
			# make predictions on the training and dev data
			train_pred = make_predictions(self, train_data)
			dev_pred = make_predictions(self, dev_data)

			per_train_f1 = class_f1_scores(train_pred, train_data)
			per_dev_f1 = class_f1_scores(dev_pred, dev_data)

			post_dev_f1 = per_dev_f1[HAS_POST]

			training_f1 = overall_f1(train_pred, train_data)
			dev_f1 = overall_f1(dev_pred, dev_data)

			if post_dev_f1 >= best_f1 and epoch > MIN_ROUND:
				best_f1 = post_dev_f1
				best_epoch = epoch
				t.save(self, model_path)

			# print out the statistics for the epoch
			print(" Loss: %7.6f |" % (total_loss / len(train_data)), end="")
			print(" Train F1 %4.4f & %4.4f = %4.4f |" % (per_train_f1[NO_POST], per_train_f1[HAS_POST], training_f1), end="")
			print(" Dev F1 %4.4f & %4.4f = %4.4f |" % (per_dev_f1[NO_POST], per_dev_f1[HAS_POST], dev_f1), end="")
			print(" Time: %8.2f" % (time() - start_time), "seconds")
			epoch += 1
			
		self.eval()

		print("Loading model from epoch %d" % best_epoch)
		best = t.load(model_path, weights_only=False)

		return best


	def num_parameters(self):
		"""
		Returns the number of parameters the model has
		"""
		return sum(np.prod(p.size()) for p in self.parameters() if p.requires_grad)


class Mk5(Model):

	def __init__(self, hidden):
		super().__init__()

		class_weights = t.tensor([1.0, 1.5])
		self.hidden = hidden

		self.sequential = nn.Sequential(
			nn.BatchNorm2d(3),
			nn.Conv2d(3, hidden, 5, 2, 2),
			nn.ReLU(),
			nn.AvgPool2d(2, 2, 0),
			nn.Conv2d(hidden, hidden, 5, 2, 2),
			nn.ReLU(),
			nn.AvgPool2d(2, 2, 0),
			nn.BatchNorm2d(hidden),
			nn.Conv2d(hidden, hidden, 5, 2, 2),
			nn.ReLU(),
			nn.AvgPool2d(2, 2, 0),
			nn.BatchNorm2d(hidden),
			nn.Conv2d(hidden, hidden, 5, 1, 1),
			nn.ReLU())
		self.lstm = nn.LSTM(70*hidden, hidden, bidirectional=True)
		self.mlp = nn.Sequential(nn.Linear(2*hidden, hidden),
			nn.ReLU(),
			nn.Linear(hidden, hidden),
			nn.ReLU(),
			nn.Linear(hidden, 2))
		self.loss_function = nn.CrossEntropyLoss()

	def forward(self, tensor):
		"""
		Applies the model to the given tensor
		"""
		batch_size, _, _, _ = tensor.size()
		tensor = self.sequential(tensor)
		tensor = t.reshape(tensor, (batch_size, 70*self.hidden))
		tensor, _ = self.lstm(tensor)
		tensor = self.mlp(tensor)

		return tensor

class VGG16(Model):

	def __init__(self, hidden, class_weights):
		super().__init__()

		self.class_weights = class_weights

		self.hidden = hidden
		self.sequential = nn.Sequential(
			nn.BatchNorm2d(3),
			nn.Conv2d(3, hidden, 3, 1, 2),
			nn.ReLU(),
			nn.Conv2d(hidden, hidden, 3, 1, 2),
			nn.ReLU(),
			nn.MaxPool2d(2, 2, 1),
			nn.BatchNorm2d(hidden),

			nn.Conv2d(hidden, hidden, 3, 1, 2),
			nn.ReLU(),
			nn.Conv2d(hidden, hidden, 3, 2, 2),
			nn.ReLU(),
			nn.MaxPool2d(2, 2, 1),
			nn.BatchNorm2d(hidden),

			nn.Conv2d(hidden, hidden, 3, 1, 2),
			nn.ReLU(),
			nn.Conv2d(hidden, hidden, 3, 1, 2),
			nn.ReLU(),
			nn.Conv2d(hidden, hidden, 3, 2, 2),
			nn.ReLU(),
			nn.MaxPool2d(2, 2, 1),
			nn.BatchNorm2d(hidden),

			nn.Conv2d(hidden, hidden, 3, 1, 2),
			nn.ReLU(),
			nn.Conv2d(hidden, hidden, 3, 1, 2),
			nn.ReLU(),
			nn.Conv2d(hidden, hidden, 3, 2, 2),
			nn.ReLU(),
			nn.MaxPool2d(2, 2, 1),
			nn.BatchNorm2d(hidden),

			nn.Conv2d(hidden, hidden, 3, 1, 2),
			nn.ReLU(),
			nn.Conv2d(hidden, hidden, 3, 1, 2),
			nn.ReLU(),
			nn.Conv2d(hidden, hidden, 3, 2, 2),
			nn.ReLU(),
			nn.MaxPool2d(2, 2, 1),
			nn.BatchNorm2d(hidden))
		self.sequential2 = nn.Sequential(nn.Linear(20*hidden, hidden),
			nn.ReLU(),
			nn.Linear(hidden, 2))
		self.loss_function = nn.CrossEntropyLoss(self.class_weights)

	def forward(self, tensor):
		"""
		Applies the model to the given tensor
		"""
		batch, _, _, _ = tensor.size()
		tensor = self.sequential(tensor)
		tensor = t.reshape(tensor, (batch, 20 * self.hidden))
		tensor = self.sequential2(tensor)

		return tensor


class ResNetBase(Model):
	"""
	A base template for Resnet style models
	"""

	def __init__(self, init_filters: int, filter_groups: list[tuple[int, int]], channels: int, flat_size: int):
		"""
		Initialize the model
		filter_groups - a list of (num layers, num filters)
		"""
		super().__init__()

		HIDDEN = 32

		self.flat = flat_size
		self.hidden = HIDDEN
		class_weights = t.tensor([1.0, 1.5])
		# set up the basic input layers
		layers = [nn.Conv2d(channels, init_filters, 7), nn.ReLU(inplace=True), nn.MaxPool2d(3, 2)]

		prev_dim = init_filters

		start_stride = 1

		# all the layer groups
		for num_layers, filters in filter_groups:
			layers += self.make_groups(num_layers, prev_dim, filters, start_stride)
			prev_dim = filters
			start_stride = 2

		self.layers = nn.Sequential(*layers)
		self.size = prev_dim

		self.mlp= nn.Sequential(nn.Linear(flat_size * self.size, HIDDEN),
								nn.ReLU(),
								nn.Linear(HIDDEN, HIDDEN),
								nn.ReLU(),
								nn.Linear(HIDDEN, 2))

		self.loss_function = nn.CrossEntropyLoss(class_weights)

	def forward(self, source_tensor):
		"""
		Applies the ResNet model on the image_tensor
		"""
		batch, _, _, _ = source_tensor.size()
		repr = self.layers(source_tensor)

		#TODO remove
		#print(repr.size())

		flat_repr = t.reshape(repr, (batch, self.flat * self.size))
		return self.mlp(flat_repr)

	def make_groups(self, num_layers: int, channels_in: int, filters: int, start_stride: int):
		"""
		Makes a block of layers with the same number of filters
		"""

		const = PreActivationResNetBlock

		layers = [const(channels_in, filters, start_stride)]

		# add in each layer
		for _ in range(num_layers - 1):
			layers.append(const(filters, filters, 1))

		return layers


class PreActivationResNetBlock(nn.Module):
	"""
	A 'pre-activation' ResNet block
	"""

	def __init__(self, input_channels: int, filters: int, stride: int):
		"""
		Initialize ResNet Block - two layers of 1D convolutions
		"""
		super().__init__()

		WINDOW_SIZE = 3
		PAD = 1

		self.filters = filters
		self.input_channels = input_channels
		self.stride = stride

		self.stack = nn.Sequential(nn.BatchNorm2d(self.input_channels),
									nn.ReLU(inplace=True),
									nn.Conv2d(self.input_channels, self.filters, WINDOW_SIZE, self.stride, PAD),
									nn.BatchNorm2d(self.filters),
									nn.ReLU(inplace=True),
									nn.Conv2d(self.filters, self.filters, WINDOW_SIZE, 1, PAD))

		# if the stide is greater than 1 or there is a difference
		# in the input/output channel size, a projection is needed
		if self.stride > 1 or filters != input_channels:
			self.downsample = nn.Conv2d(self.input_channels, self.filters, 1, self.stride)
		else:
			self.downsample = None

	def forward(self, matrix):
		"""
		Applies ResNet to the image-set matrix
		"""
		identity = matrix
		output = self.stack(matrix)

		# down sample if needed:
		if self.downsample:
			identity = self.downsample(matrix)

		return identity + output

	def __repr__(self):
		return "Preactivation ResNet %d %s" % (self.filters, self.stack)


class ResNet18(ResNetBase):
	"""
	An 18 layer Resnet model
	"""
	def __init__(self):
		#super().__init__(64, [(2, 33), (2, 32), (3, 32), (2, 32)], RGB, 37*50)
		super().__init__(64, [(1, 32), (2, 32), (1, 32), (1, 32), (1, 32), (1, 32)], RGB, 130)

	def __repr__(self):
		return super().__repr__() + "Resnet-18"
