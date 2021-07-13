
"""
A module to predict bay
"""

import itertools as it
import numpy as np
import pandas as pd

from sklearn import ensemble
from sklearn.model_selection import train_test_split

from common import COLUMNS, to_ord

# These ideally would be derived : )
# TODO: pull these values from a csv or somewhere
NUM_VINES = 84
VINES_PER_BAY = 4
FIRST_BAY = 4.5

# I hand labeled this date's bays
LABELED_DATE = "2019-06-12"


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


def prep_data(df):
	"""
	prep_data returns the training and prediction columns derived from the dataframe.
	"""

	# Generate an ordinal row
	df["ts"] = df["time"].apply(to_ord)
	df["ts"] /= np.max(df["ts"])

	# Fill in some values
	df = df.sort_values(["camera", "ts"])
	df["camera"] = df["camera"].interpolate()
	df["row"] = df["row"].interpolate()

	# Calculate relative latitude in [0, 1] range for block
	df["rel_lat"] = df["lat"] - np.min(df["lat"])
	df["rel_lat"] = df["rel_lat"] / np.max(df["rel_lat"])
	df["dir"] = False

	for cam, row in it.product(df["camera"].unique(), df["row"].unique()):
		idx = np.logical_and(df["camera"] == cam, df["row"] == row)

		# Scale the latitude into an approximate vine number
		lats = df.loc[idx, "lat"]
		lats -= np.min(lats)
		lats *= NUM_VINES / np.max(lats)
		df.loc[idx, "p_bay"] = lats.apply(pred_bay)

		# Calculate relative latitude in [0, 1] range for row
		df.loc[idx, "rel_lat"] -= np.min(df.loc[idx, "rel_lat"])
		df.loc[idx, "rel_lat"] /= np.max(df.loc[idx, "rel_lat"])

		# Scale to the relative time spent walking that row
		ts = df.loc[idx, "ts"]

		#TODO this needs a comment...
		ts = -ts if (row % 2) == 0 else ts
		ts -= np.min(ts)
		ts /= np.max(ts)
		df.loc[idx, "rel_ts"] = ts

		# TODO why gradient? this need a lot more explanation
		# Calculate the direction of travel for the row
		df.loc[idx, "dir"] = np.median(np.gradient(df.loc[idx, "lat"])) > 0

	return df[["p_bay", "lon", "rel_ts", "dir", "rel_lat"]], df["bay"]


def train_model(f_org, model, vineyard="crawford-beck", block=9):
	"""
	train_model opens the labeled date of images and trains the given model to predict
	bays.
	"""

	# Train a random forest on the hand labeled data
	training_data = f_org.get_label_file(vineyard, block, LABELED_DATE)
	training = pd.read_csv(training_data, index_col=False)
	training = training[training["bay"].notna()]

	features, labels = prep_data(training)

	print("Training model on hand-labeled date: %s" % LABELED_DATE)

	# Train on 80% of the data
	x_train, x_test, y_train, y_test = train_test_split(features, labels, test_size=0.2)
	model.fit(x_train, y_train)

	# Evaluate the model on the test data
	score = model.score(x_test, y_test)
	print("Trained model with accuracy: %02.3f" % (100 * score))

	return model, score


def predict(f_org, vineyard, block, date, df=None):
	"""
	main trains a bay predictor model on the hand-labeled data and predics the bays of
	the data being ingested.
	"""

	# Open the current csv
	label_file = f_org.get_label_file(vineyard, block, date)
	
	if df is None:
		df = pd.read_csv(label_file, index_col=False)

	print("Predicting Bays")

	# Train a bay predictor on hand-labeled data from 2019
	model, _ = train_model(f_org, ensemble.RandomForestClassifier(), vineyard, block)

	# Use the trained forest to predict bays
	try:
		features, _ = prep_data(df)
		df["pred_bay"] = model.predict(features)
		print("Writing bay predictions")

	#TODO fix this
	except:
		print("GPS Data too corrupt to predict bays")
		print("rerun with -s param to walk through ingest steps and view csv file")

	df[COLUMNS].to_csv(label_file)

	return df[COLUMNS]
