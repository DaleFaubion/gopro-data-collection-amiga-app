from time import time
from typing import Union
import torch as t
import torch.nn as nn
from torch.optim import Adam
from torchvision.transforms import Resize
from torchvision import transforms as tt
import numpy as np

from quant import make_predictions, overall_f1

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
		optim = Adam(params, learning_rate, weight_decay=reg)
		best_f1 = 0.0
		best_epoch = 0
		self.train()
		epoch = 1

		# setup transformations to augment the data
		transform = tt.Compose([
								 #tt.RandomRotation(10),
								 #tt.RandomHorizontalFlip(),
								 #tt.RandomPerspective(.1)  #causes warning
								 #tt.ColorJitter(.3, .1, .1, .1),
								 #tt.GaussianBlur((5,5), (0.001, .5))
								])
		
		# for a fixed number of epochs, train the model
		while epoch <= num_epochs:
			print("Epoch %4d |" % epoch, end="")
			start_time = time()
			total_loss = 0.0
			
			train_data.shuffle()
			
			# for each training example, make a prediction, measure the loss, and update
			for inst, target in train_data:
				self.zero_grad()
				pred = self(transform(inst.cuda()))

				#TODO debug
				#print("Debug, target", target, "pred", pred.cpu().data.numpy().argmax(), pred.cpu().data)

				loss = self.loss_function(pred, target.cuda())
				total_loss += loss.cpu().data.item()
				loss.backward()
				optim.step()
			

			# make predictions on the training and dev data
			training_f1 = overall_f1(make_predictions(self, train_data), train_data)
			dev_f1 = overall_f1(make_predictions(self, dev_data), dev_data)

			if dev_f1 > best_f1 and epoch > MIN_ROUND:
				best_f1 = dev_f1
				best_epoch = epoch
				t.save(self, model_path)

			# print out the statistics for the epoch
			print(" Loss: %7.4f |" % (total_loss / len(train_data)), end="")
			print(" Train F1 %4.4f |" % training_f1, end="")
			print(" Dev F1 %4.4f |" % dev_f1, end="")
			print(" Time: %8.2f" % (time() - start_time), "seconds")
			epoch += 1
			
		self.eval()

		print("Loading model from epoch %d" % best_epoch)
		best = t.load(model_path)

		return best


	def num_parameters(self):
		"""
		Returns the number of parameters the model has
		"""
		return sum(np.prod(p.size()) for p in self.parameters() if p.requires_grad)



class Mk2(Model):

	def __init__(self, hidden):
		super().__init__()
		class_weights = t.tensor([1.0, 200.0])

		self.resize = Resize([300, 400])

		self.hidden = hidden
		self.conv2d = nn.Conv2d(3, hidden, 9, 1, 4)
		self.maxpool2d = nn.MaxPool2d(4, 2, 2)
		self.conv2d2 = nn.Conv2d(hidden, hidden, 7, 1, 3)
		self.maxpool2d2 = nn.MaxPool2d(4, 2, 1)
		self.conv2d3 = nn.Conv2d(hidden, hidden, 5, 1, 2)
		self.maxpool2d3 = nn.MaxPool2d(3, 2, 1)
		self.conv2d4 = nn.Conv2d(hidden, hidden, 3, 1, 1)
		self.maxpool2d4 = nn.MaxPool2d(3, 2, 1)
		self.conv2d5 = nn.Conv2d(hidden, hidden, 3, 1, 1)
		self.maxpool2d5 = nn.MaxPool2d(3, 2, 1)
		self.linear = nn.Linear(130*hidden, hidden)
		self.relu = nn.ReLU()
		self.linear2 = nn.Linear(hidden, hidden)
		self.relu2 = nn.ReLU()
		self.linear3 = nn.Linear(hidden, 2)
		self.loss_function = nn.CrossEntropyLoss(class_weights)
	
	def forward(self, tensor):
		"""
		Applies the model to the given tensor
		"""
		tensor = self.resize(tensor)
		tensor = self.conv2d(tensor)
		tensor = self.maxpool2d(tensor)
		tensor = self.conv2d2(tensor)
		tensor = self.maxpool2d2(tensor)
		tensor = self.conv2d3(tensor)
		tensor = self.maxpool2d3(tensor)
		tensor = self.conv2d4(tensor)
		tensor = self.maxpool2d4(tensor)
		tensor = self.conv2d5(tensor)
		tensor = self.maxpool2d5(tensor)
		tensor = tensor.squeeze(0)
		tensor = t.reshape(tensor, (130*self.hidden,))
		tensor = self.linear(tensor)
		tensor = self.relu(tensor)
		tensor = self.linear2(tensor)
		tensor = self.relu2(tensor)
		tensor = self.linear3(tensor)

		return tensor

class Mk3(Model):

	def __init__(self, hidden):
		super().__init__()
		class_weights = t.tensor([1.0, 200.0])

		self.resize = Resize([300, 400])

		self.hidden = hidden
		self.sequential = nn.Sequential(nn.Conv2d(3, hidden, 9, 1, 4),
			nn.MaxPool2d(4, 2, 2),
			nn.Conv2d(hidden, hidden, 7, 1, 3),
			nn.MaxPool2d(4, 2, 1))

		self.mlp= nn.Sequential(nn.Linear(7500*hidden, hidden),
			nn.ReLU(),
			nn.Linear(hidden, hidden),
			nn.ReLU(),
			nn.Linear(hidden, 2))
		
		self.loss_function = nn.CrossEntropyLoss(class_weights)
	
	def forward(self, tensor):
		"""
		Applies the model to the given tensor
		"""
									
		tensor = self.resize(tensor)
		tensor = self.sequential(tensor)
		tensor = t.reshape(tensor, (7500*self.hidden,))
		tensor = self.mlp(tensor)

		return tensor

class Mk4(Model):

	def __init__(self, hidden):
		super().__init__()

		class_weights = t.tensor([1.0, 200.0])

		self.resize = Resize([300, 400])

		self.hidden = hidden
		self.sequential = nn.Sequential(nn.Conv2d(3, hidden, 5, 2, 2),
			nn.ReLU(),
			nn.AvgPool2d(2, 2, 0),
			nn.Conv2d(hidden, hidden, 5, 2, 2),
			nn.ReLU(),
			nn.AvgPool2d(2, 2, 0),
			nn.Conv2d(hidden, hidden, 5, 2, 2),
			nn.ReLU(),
			nn.AvgPool2d(2, 2, 0))
		self.mlp = nn.Sequential(nn.Linear(30*hidden, hidden),
			nn.ReLU(),
			nn.Linear(hidden, hidden),
			nn.ReLU(),
			nn.Linear(hidden, 2))
		self.loss_function = nn.CrossEntropyLoss(class_weights)

	def forward(self, tensor):
		"""
		Applies the model to the given tensor
		"""
		tensor = self.resize(tensor)
		tensor = self.sequential(tensor)
		tensor = tensor.squeeze(0)
		tensor = t.reshape(tensor, (30*self.hidden,))
		tensor = self.mlp(tensor)

		return tensor


class VggNarrow(Model):

	def __init__(self, hidden):
		super().__init__()
		class_weights = t.tensor([1.0, 200.0])

		self.resize = Resize([300, 400])

		self.hidden = hidden
		self.sequential = nn.Sequential(nn.Conv2d(3, hidden, 3, 1, 1),
			nn.ReLU(),
			nn.Conv2d(hidden, hidden, 3, 1, 1),
			nn.ReLU(),
			nn.MaxPool2d(2, 2, 0),
			nn.Conv2d(hidden, hidden, 3, 1, 1),
			nn.ReLU(),
			nn.Conv2d(hidden, hidden, 3, 1, 1),
			nn.ReLU(),
			nn.MaxPool2d(2, 2, 0),
			nn.Conv2d(hidden, hidden, 3, 1, 1),
			nn.ReLU(),
			nn.Conv2d(hidden, hidden, 3, 1, 1),
			nn.ReLU(),
			nn.MaxPool2d(2, 2, 0),
			nn.Conv2d(hidden, hidden, 3, 1, 1),
			nn.ReLU(),
			nn.Conv2d(hidden, hidden, 3, 1, 1),
			nn.ReLU(),
			nn.MaxPool2d(2, 2, 0))

		self.mlp = nn.Sequential(nn.Linear(450*hidden, hidden),
			nn.ReLU(),
			nn.Linear(hidden, hidden),
			nn.ReLU(),
			nn.Linear(hidden, 2)
			)
		
		self.loss_function = nn.CrossEntropyLoss(class_weights)

	def forward(self, tensor):
		"""
		Applies the model to the given tensor
		"""
		tensor = self.resize(tensor)
		tensor = self.sequential(tensor)
		tensor = tensor.squeeze(0)
		tensor = t.reshape(tensor, (450*self.hidden,))
		tensor = self.mlp(tensor)

		return tensor


#NOTE: this needs to be double checked...
BOTTLENECK_EXP = 2

DownSampler = Union[nn.Conv2d, None]

class ResNetBase(Model):
	"""
	A base template for Resnet style models
	"""
	def __init__(self, init_filters: int, filter_groups: list[tuple[int, int]], channels, bottleneck=False):
		"""
		Initialize the model
		filter_groups - a list of (num layers, num filters)
		"""
		#the second item of the last tuple is the number of filters outputted
		#by this model
		#NOTE this the size will later be overwritten
		super().__init__()

		self.bottleneck = bottleneck

		class_weights = t.tensor([1.0, 200.0])

		self.resize = Resize([300, 400])

		#setup the basic input layers
		layers = [nn.Conv2d(channels, init_filters, 7, 2, 1), nn.ReLU(inplace=True), nn.MaxPool2d(3, 2)]

		prev_dim = init_filters
	
		start_stride = 1

		exp = BOTTLENECK_EXP if bottleneck else 1

		#all the layer groups
		for num_layers, filters in filter_groups:

			layers += self.make_groups(num_layers, prev_dim, filters, start_stride)
			prev_dim = filters * exp
			start_stride = 2

		self.layers = nn.Sequential(*layers)
		self.size = prev_dim
		self.loss_function = nn.CrossEntropyLoss(class_weights)


	def forward(self, source_tensor):
		"""
		Applies the ResNet model on the image_tensor
		"""
		return self.layers(self.resize(source_tensor))


	def make_groups(self, num_layers: int, channels_in: int, filters: int, start_stride: int):
		"""
		Makes a block of layers with the same number of filters
		"""

		const = ResNetBottleneckBlock if self.bottleneck else PreActivationResNetBlock

		layers = [const(channels_in, filters, start_stride)]
		
		exp = BOTTLENECK_EXP if self.bottleneck else 1

		#add in each layer
		for _ in range(num_layers-1):
			layers.append(const(filters*exp, filters, 1))

		return layers

	def __repr__(self):
		return "Image Model: Resnet %s" % self.layers


#TODO need to finish with MLP
class ResNet8(ResNetBase):
	"""
	An 8 layer Resnet model
	"""
	def __init__(self, channels):
		super().__init__(64, [(1, 64), (1, 128), (1, 256), (1, 512)], channels)

	def __repr__(self):
		return super().__repr__() + "Resnet-8"


class ResNet18(ResNetBase):
	"""
	An 18 layer Resnet model
	"""
	def __init__(self, channels):
		super().__init__(64, [(2, 64), (2, 128), (2, 256), (2, 512)], channels)

		hidden = 512
		self.hidden = hidden
		
		self.mlp= nn.Sequential(nn.Linear(130*hidden, hidden),
			nn.ReLU(),
			nn.Linear(hidden, hidden),
			nn.ReLU(),
			nn.Linear(hidden, 2))

	def forward(self, tensor):
		tensor = super().forward(tensor)
		tensor = tensor.squeeze(0)
		tensor = t.reshape(tensor, (130*self.hidden,))
		tensor = self.mlp(tensor)

		return tensor


	def __repr__(self):
		return super().__repr__() + "Resnet-18"

#TODO need to finish with NLP
class ResNet34(ResNetBase):
	"""
	An 34 layer Resnet model
	"""
	def __init__(self, channels):
		super().__init__(64, [(3, 64), (4, 128), (6, 256), (3, 512)], channels)


	def __repr__(self):
		return super().__repr__() + "Resnet-34"

#TODO finish with MLP
class ResNet50(ResNetBase):
	"""
	A 50 Layer ResNet model
	"""
	def __init__(self, channels):
		super().__init__(64, [(3, 64), (4, 128), (6, 256), (3, 512)], channels, True)


	def __repr__(self):
		return super().__repr__() + "Resnet-50"

#TODO finish with MLP
class ResNet101(ResNetBase):
	"""
	A 101 Layer Resnet model
	"""
	def __init__(self, channels):
		super().__init__(64, [(3, 64), (4, 128), (23, 256), (3, 512)], channels, True)


	def __repr__(self):
		return super().__repr__() + "Resnet-101"

#TODO finish with MLP
class ResNet152(ResNetBase):
	"""
	A 152 Layer Resnet model
	"""
	def __init__(self, channels):
		super().__init__(64, [(3, 64), (8, 128), (36, 256), (3, 512)], channels, True)


	def __repr__(self):
		return super().__repr__() + "Resnet-152"


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

		#if the stide is greater than 1 or there is a difference
		#in the input/output channel size, a projection is needed
		if self.stride > 1 or filters != input_channels:
			self.downsample: DownSampler = nn.Conv2d(self.input_channels, self.filters, 1, self.stride)
		else:
			self.downsample: DownSampler = None


	def forward(self, matrix):
		"""
		Applies ResNet to the image-set matrix
		"""
		identity = matrix
		output = self.stack(matrix) 

		#downsample if needed:
		if self.downsample:
			identity = self.downsample(matrix)
	
		return identity + output


	def __repr__(self):
		return "Preactivation ResNet %d %s" % (self.filters, self.stack)


class ResNetBottleneckBlock(nn.Module):
	"""
	A 'pre-activation' ResNet 'bottleneck' block
	"""
	def __init__(self, input_channels: int, filters: int, stride: int):
		"""
		Initialize ResNet Block - 3 layers of 1D convolutions
		"""
		super().__init__()

		SMALL_WINDOW = 1
		WINDOW_SIZE = 3
		PAD = 1

		self.filters = filters
		self.input_channels = input_channels
		self.stride = stride

		final_out = self.filters * BOTTLENECK_EXP

		self.stack = nn.Sequential(nn.BatchNorm2d(self.input_channels),
											nn.ReLU(inplace=True),
											nn.Conv2d(self.input_channels, self.filters, SMALL_WINDOW),
											
											nn.BatchNorm2d(self.filters),
											nn.ReLU(inplace=True),
											nn.Conv2d(self.filters, self.filters, WINDOW_SIZE, self.stride, PAD),
											
											nn.BatchNorm2d(self.filters),
											nn.ReLU(inplace=True),
											nn.Conv2d(self.filters, final_out, SMALL_WINDOW))


		#if the stide is greater than 1 or there is a difference
		#in the input/output channel size, a projection is needed
		if self.stride > 1 or filters != final_out:
			self.downsample: DownSampler = nn.Conv2d(self.input_channels, final_out, 1, self.stride)
		else:
			self.downsample: DownSampler = None


	def forward(self, matrix):
		"""
		Applies ResNet to the image-set matrix
		"""
		identity = matrix
		output = self.stack(matrix) 

		#downsample if needed:
		if self.downsample:
			identity = self.downsample(matrix)
	
		return identity + output


	def __repr__(self):
		return "Bottleneck ResNet %d %s" % (self.filters, self.stack)
