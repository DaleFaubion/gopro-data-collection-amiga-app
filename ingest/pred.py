"""
A module for predicting the row or bay each image
"""

import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

from ingest.common import to_ord, COLUMNS
from ingest.fix import normalize


def plot_images(data, filename, col):
	"""
	Plot the row/bay data according to lat/lon
	"""	
	plt.figure(figsize=(10,10))

	# for each row plot the image locations
	for row in data[col].unique():

		current = data[col] == row

		plt.scatter(data.loc[current, "lat"], data.loc[current, "lon"], s=5)
	
	plt.title("%s of Images" % col.title())
	plt.savefig(filename)
	plt.close()


def prep_data(data):
	"""
	Prepare the data for predicting the rows/bays
	"""
	# setup the time series
	data["ts"] = data["time"].apply(to_ord)
	data["ts"] = data["ts"].interpolate()

	# start the time at zero
	data["ts_norm"] = data["ts"] - data["ts"].min()

	return data


def make_features(data):
	"""
	Returns the features for predicting the row/bay, assumes prep_data
	has been run first
	"""
	features = pd.DataFrame()

	features["ts_norm"] = data["ts_norm"]
	features["lat"] = normalize(data["lat"])
	features["lon"] = normalize(data["lon"])

	return features


def train_model(model, training_data, col):
	"""
	Trains a model to predict the rows/bays
	"""

	features = make_features(training_data)
	labels = training_data[col]
	
	# split the data into training/testing
	x_train, x_test, y_train, y_test = train_test_split(features, labels, \
		test_size=0.2, stratify=labels)

	# fit the model to the data
	model.fit(x_train, y_train)

	# evaluate the model on the test data
	y_pred = model.predict(x_test)

	score = f1_score(y_test, y_pred, average="micro")

	# print the results
	print("%s F1 Score %f" % (col.title(), score))

	return model


def predict(data, labeled_data, col):
	"""
	Predicts the row/bay numbers from the ingested gps data.
	"""
	# plot the labeled data's rows/bays
	plot_images(labeled_data, "hand_labeled_%s.png" % col, col)

	# prep the labeled data
	labeled_data = prep_data(labeled_data)

	# train the model on the labeled data
	model = train_model(RandomForestClassifier(), labeled_data, col)

	data = prep_data(data)

	# predict the rows/bays on the data
	data[col] = model.predict(make_features(data))

	# plot the predicted rows/bays
	plot_images(data, "predicted_%s.png" % col, col)

	return data[COLUMNS]
