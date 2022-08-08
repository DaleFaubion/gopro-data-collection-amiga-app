
"""
A module for quantifying error
"""
import torch as t
from sklearn.metrics import f1_score

NAMES = ["No post", "Has post"]

def overall_f1(predictions, gold_data):
	"""
	Calculates and returns the overall F1 score
	"""
	return f1_score(predictions, [l.data.numpy() for _, l in gold_data], average="micro")


def class_f1_scores(predictions, gold_data):
	"""
	Calculates and returns the F1 score per class (0/1)
	"""
	return f1_score(predictions, [l for _, l in gold_data], average=None)


def make_predictions(model, dataset):
	"""
	Makes predicitons for the whole dataset and returns a list of predictions
	"""
	predictions = []

	with t.no_grad():
		model.eval()

		# for each image in the dataset make a prediction
		for image, _ in dataset:
			
			pred = model(image.cuda()).cpu().data.numpy()

			predictions.append(pred.argmax())

	return predictions
