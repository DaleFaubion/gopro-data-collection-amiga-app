from time import time
from typing import Union
import torch as t
import torch.nn as nn
from torch.optim import SGD
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
			training_f1 = overall_f1(make_predictions(self, train_data), train_data)
			dev_f1 = overall_f1(make_predictions(self, dev_data), dev_data)

			if dev_f1 >= best_f1 and epoch > MIN_ROUND:
				best_f1 = dev_f1
				best_epoch = epoch
				t.save(self, model_path)

			# print out the statistics for the epoch
			print(" Loss: %7.6f |" % (total_loss / len(train_data)), end="")
			print(" Train F1 %4.4f |" % training_f1, end="")
			print(" Dev F1 %4.4f |" % dev_f1, end="")
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
			nn.Conv2d(hidden, hidden, 5, 2, 2),
			nn.ReLU(),
			nn.AvgPool2d(2, 2, 0),
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
