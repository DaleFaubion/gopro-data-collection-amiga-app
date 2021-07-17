
"""
A module to predict bay
"""

import itertools as it
import numpy as np

from sklearn import ensemble
from sklearn.model_selection import train_test_split

from ingest.common import COLUMNS, to_ord

# These ideally would be derived : )
# TODO: pull these values from a csv or somewhere
NUM_VINES = 84
VINES_PER_BAY = 4
FIRST_BAY = 4.5


def pred_bay(latitude):
	"""
	pred_bay does a rough estimate of the bay number based on latitude only and the
	known bay spacing.
	"""
	result = None

	if latitude < FIRST_BAY:
		result = 1
	
	else:
		if latitude > NUM_VINES:
			latitude = NUM_VINES 

		#TODO figure this out and explain this...
		result = 2 + int((latitude - FIRST_BAY) / VINES_PER_BAY)
	
	return result

#TODO what does this do?
def prep_data(data):
	"""
	prep_data returns the training and prediction columns derived from the dataframe.
	"""

	# Generate an ordinal row
	data["ts"] = data["time"].apply(to_ord)
	data["ts"] /= np.max(data["ts"])

	# Fill in some values
	data = data.sort_values(["camera", "ts"])
	data["camera"] = data["camera"].interpolate()
	data["row"] = data["row"].interpolate()

	# Calculate relative latitude in [0, 1] range for block
	data["rel_lat"] = data["lat"] - np.min(data["lat"])
	data["rel_lat"] = data["rel_lat"] / np.max(data["rel_lat"])
	data["dir"] = False

	for cam, row in it.product(data["camera"].unique(), data["row"].unique()):
		idx = np.logical_and(data["camera"] == cam, data["row"] == row)

		# Scale the latitude into an approximate vine number
		lats = data.loc[idx, "lat"]
		lats -= np.min(lats)
		lats *= NUM_VINES / np.max(lats)
		data.loc[idx, "p_bay"] = lats.apply(pred_bay)

		# Calculate relative latitude in [0, 1] range for row
		data.loc[idx, "rel_lat"] -= np.min(data.loc[idx, "rel_lat"])
		data.loc[idx, "rel_lat"] /= np.max(data.loc[idx, "rel_lat"])

		# Scale to the relative time spent walking that row
		ts = data.loc[idx, "ts"]

		#TODO this needs a comment...
		ts = -ts if (row % 2) == 0 else ts
		ts -= np.min(ts)
		ts /= np.max(ts)
		data.loc[idx, "rel_ts"] = ts

		# TODO why gradient? this need a lot more explanation
		# Calculate the direction of travel for the row
		data.loc[idx, "dir"] = np.median(np.gradient(data.loc[idx, "lat"])) > 0

	return data[["p_bay", "lon", "rel_ts", "dir", "rel_lat"]], data["bay"]


def train_model(model, training):
	"""
	train_model opens the labeled date of images and trains the given model to predict
	bays.
	"""

	# Train a random forest on the hand labeled data
	features, labels = prep_data(training)

	print("Training model on hand-labeled data")

	# Train on 80% of the data
	x_train, x_test, y_train, y_test = train_test_split(features, labels, test_size=0.2)
	model.fit(x_train, y_train)

	# Evaluate the model on the test data
	score = model.score(x_test, y_test)
	print("Trained model with accuracy: %02.3f" % (100 * score))

	return model, score


def predict(data, labeled_data):
	"""
	Trains a bay predictor model on the hand-labeled data and predics the bays of
	the data being ingested.
	"""

	print("Predicting Bays")

	# Train a bay predictor on hand-labeled data from 2019
	model, _ = train_model(ensemble.RandomForestClassifier(), labeled_data)

	# Use the trained forest to predict bays
	try:
		features, _ = prep_data(data)
		data["pred_bay"] = model.predict(features)
		print("Making bay predictions")

	#TODO fix this
	except:
		print("GPS Data too corrupt to predict bays")

	return data[COLUMNS]
