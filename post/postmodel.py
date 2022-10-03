from time import time
import torch as t
import torch.nn as nn
from torch.optim import Adam
from torchvision.transforms import Resize
import numpy as np

from quant import make_predictions, overall_f1

MODEL_PATH = "best_model.p"

RGB=3

class Model(nn.Module):

	def __init__(self):
		super().__init__()
	
	def fit(self, train_data, dev_data, num_epochs, learning_rate, reg):
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
		
		
		# for a fixed number of epochs, train the model
		while epoch <= num_epochs:
			print("Epoch %4d |" % epoch, end="")
			start_time = time()
			total_loss = 0.0
			
			train_data.shuffle()
			
			# for each training example, make a prediction, measure the loss, and update
			for inst, target in train_data:
				self.zero_grad()
				pred = self(inst.cuda())

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
				t.save(self, MODEL_PATH)

			# print out the statistics for the epoch
			print(" Loss: %7.4f |" % (total_loss / len(train_data)), end="")
			print(" Train F1 %4.4f |" % training_f1, end="")
			print(" Dev F1 %4.4f |" % dev_f1, end="")
			print(" Time: %8.2f" % (time() - start_time), "seconds")
			epoch += 1
			
		self.eval()

		print("Loading model from epoch %d" % best_epoch)
		best = t.load(MODEL_PATH)

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
