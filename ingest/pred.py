"""
A module for predicting the row or bay each image
"""

from os.path import join

import math
import numpy as np
import pandas as pd
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
	plt.figure(figsize=(20,20))

	# for each row plot the image locations
	for row in data[col].unique():

		current = data[col] == row

		plt.scatter(data.loc[current, "lat"], data.loc[current, "lon"], label="%s %d" % (col, row), s=2)
	
	plt.title("%s of Images" % col.title())
	plt.legend()
	plt.savefig(filename)
	plt.close()


def prep_data(data):
	"""
	Prepare the data for predicting the rows/bays
	"""
	# setup the time series
	data["ts"] = data["time"].apply(to_ord)
	data["ts"] = data["ts"].interpolate()

	# make a map from time stamp to position
	time = enumerate(sorted(data["ts"].to_numpy()))

	# make the sequence position map
	time_map = {t:i for i,t in time}

	# start the time at zero, count up one at a time
	data["ts_norm"] = data["ts"].apply(lambda t: time_map[t])

	#do a reverse time series
	data["ts_rev"] = data["ts_norm"].max() - data["ts_norm"]

	return data


def make_features(data, exp_pic_per_row, max_bay):
	"""
	Returns the features for predicting the row/bay, assumes prep_data
	has been run first
	"""
	features = pd.DataFrame()

	features["ts_norm"] = data["ts_norm"]
	features["ts_cos"] = trans_time(data["ts_norm"], exp_pic_per_row, max_bay)
	features["ts_cos_rev"] = trans_time(data["ts_rev"], exp_pic_per_row, max_bay)
	features["lat"] = normalize(data["lat"] - data["lat"].min())
	features["lon"] = normalize(data["lon"] - data["lat"].min())

	return features


def trans_time(time_ord, period, max_value):	
	"""
	Transforms the series (ints starting at 0 and up) into a cosine
	wave based on a specified period

	the period should be the expected number of pictures per row
	the max value is the largest bay index e.g. 0 to 20, 20 is the max
	"""
	# set period to one
	time_ord = (time_ord * math.pi * 2) 
	return ((np.cos((time_ord / (period * 2))) + 1) / 2) * max_value


def train_model(model, training_data, col, exp_pic_per_row, max_row):
	"""
	Trains a model to predict the rows/bays
	"""

	features = make_features(training_data, exp_pic_per_row, max_row)
	labels = training_data[col]
	
	# split the data into training/testing
	x_train, x_test, y_train, y_test = \
		train_test_split(features, labels, test_size=0.2, stratify=labels)

	# fit the model to the data
	model.fit(x_train, y_train)

	# evaluate the model on the test data
	y_pred = model.predict(x_test)

	# measure the f1 score for each group
	scores = f1_score(y_test, y_pred, average=None)

	# print all the scores
	for group, f1 in enumerate(scores):
		print("%s %d, F1 %.4f" % (col.title(), group, f1))

	print("Overall F1 %.4f" % f1_score(y_test, y_pred, average="micro"))

	return model


def predict(data, labeled_data, col, out_dir, exp_pic_per_row, max_row):
	"""
	Predicts the row/bay numbers from the ingested gps data.
	"""
	# plot the labeled data's rows/bays
	plot_images(labeled_data, join(out_dir, "hand_labeled_%s.png" % col), col)

	# prep the labeled data
	labeled_data = prep_data(labeled_data)

	predicted_col = "pred_%s" % col

	# train the model on the labeled data
	model = train_model(RandomForestClassifier(), labeled_data, col, exp_pic_per_row, max_row)

	# predict the rows/bays on the training data
	labeled_data[predicted_col] = model.predict(make_features(labeled_data, exp_pic_per_row, max_row))

	# plot the predicted rows/bays
	plot_images(labeled_data, join(out_dir, "training_data_predicted_%s.png" % col), predicted_col)

	data = prep_data(data)

	# predict the rows/bays on the data
	data[predicted_col] = model.predict(make_features(data, exp_pic_per_row, max_row))

	# plot the predicted rows/bays
	plot_images(data, join(out_dir, "predicted_%s.png" % col), predicted_col)

	return data[COLUMNS]
