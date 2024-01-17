
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
	return f1_score(predictions, [l for _, l in gold_data.flat_iter()], average="micro")


def class_f1_scores(predictions, gold_data):
	"""
	Calculates and returns the F1 score per class (0/1)
	"""
	return f1_score(predictions, [l for _, l in gold_data.flat_iter()], average=None)


def write_errors(error_file, predictions, gold_data):
	"""
	Writes all the mistakes to an error log
	"""
	with open(error_file, "w") as err_out:
		
		for pred, (path, label) in zip(predictions, gold_data.names):
			
			if pred != label:
				err_out.write("%s\n" % path)


def make_predictions(model, dataset):
	"""
	Makes predicitons for the whole dataset and returns a list of predictions
	"""
	predictions = []

	with t.no_grad():
		model.eval()

		# for each image in the dataset make a prediction
		for images, _ in dataset:
			
			pred = model(images.cuda()).cpu().data.numpy()
			
			for post_pred in pred:
				predictions.append(post_pred.argmax())
		
		model.train()

	return predictions


def ibatch(dataset, batch_size):
	"""
	Iterates over the dataset in batch-sized chunks
	"""
	for i in range(0, len(dataset), batch_size):
		chunk = dataset[i : i + batch_size]

		yield [x for x,_ in chunk], [y for _,y in chunk]
