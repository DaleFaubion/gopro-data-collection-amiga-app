"""
A module to fix the GPS coordinates and sort image entries
"""

from os.path import dirname
import pandas as pd
import numpy as np

from sklearn import ensemble as en
from sklearn.model_selection import train_test_split
from sklearn import metrics

from common import COLUMNS, to_ord, from_ord

#TODO needs a lot more comments

def pad_cameras(data):
	"""
	pad_cameras fills corrupted camera data with a camera id pulled from another image
	in the same directory.  This could be done better / take into account more than
	just the first image found.
	"""

	camera_dirs = {}

	#TODO lookup what this means (index)
	for idx in data.index:

		dir_name = dirname(data.loc[idx, "raw_dir"])

		if dir_name not in camera_dirs:
			camera_dirs[dir_name] = []

		if dirname(dir_name) not in camera_dirs:
			camera_dirs[dirname(dir_name)] = []

		if data.loc[idx, "camera"] is None or np.isnan(data.loc[idx, "camera"]):
			#TODO fix
			continue

		camera_dirs[dir_name].append(data.loc[idx, "camera"])
		camera_dirs[dirname(dir_name)].append(data.loc[idx, "camera"])

	for dr in camera_dirs:
		camera_dirs[dr] = max(set(camera_dirs[dr]), key=camera_dirs[dr].count)
	
	def get_camera(idx):
		if data.loc[idx, "camera"]:
			#TODO fix multiple returns
			return data.loc[idx, "camera"]

		image_dir = data.loc[idx, "raw_dir"]
		if dirname(image_dir) in camera_dirs:
			#TODO fix multiple returns
			return camera_dirs[dirname(image_dir)]

		return camera_dirs[dirname(dirname(image_dir))]

	return data.index.map(get_camera)


def gps_outliers(data):
	"""
	gps_outliers returns a pandas index of the gps data that is corrupted in the
	dataframe.
	"""

	lat = data["lat"] + data["lon"]

	# GPS data for a given block should be within +- 1 degree of the median,
	#  blocks are very small in terms of coordinates
	return np.logical_or(np.abs(lat - np.median(lat)) > 1, pd.isnull(lat))


def train_model(data, idx, col, model):
	"""
	train_model trains a latitude or longitude prediction model on the non-corrupted
	data.
	"""

	if idx is None:
		features, labels = data[["ts"]], data[col]
	else:
		features, labels = data.loc[idx, ["ts"]], data.loc[idx, col]

	# split into training/testing sets
	x_train, x_test, y_train, y_test = train_test_split(features, labels, test_size=0.2)

	# fit the model to the data
	model.fit(x_train, y_train)

	# Evaluate the model on the test data
	y_pred = model.predict(x_test)

	# Scale both predictions and true data to [0:1] range
	y_pred, y_test = y_pred - np.min(y_test), y_test - np.min(y_test)
	y_pred, y_test = y_pred / np.max(y_test), y_test / np.max(y_test)

	# TODO fix this metric
	score = 1 - metrics.mean_squared_error(y_test, y_pred)
	print("Trained %s model with accuracy: %02.3f" % (col, 100 * score))

	return model, score


def predict(data):
	"""
	Interpolates corrupted image metadata in the given date's csv file.
	"""

	print("Padding Camera Metadata")

	# Pads corrupted camera names, assumes that images in a directory will be from
	#  the same camera
	data["camera"] = pad_cameras(data)

	# Pad corrupted time stamps, assumes that images are named chronologically
	data = data.sort_values(["camera", "raw_dir"], ignore_index=True)

	print("Padding Timestamp Metadata")

	# Create time column for k-neighbors
	data["ts"] = data["time"].apply(to_ord)
	data["ts"] = data["ts"].interpolate()
	data["time"] = data["ts"].apply(from_ord)

	print("Padding GPS Metadata")

	# Get the corrupted gps data indices
	corrupt_gps = gps_outliers(data)

	#TODO fix this
	# Correct corrputed latitude / longitude
	for camera in data["camera"].dropna().unique():
		
		# Get the index of valid gps data
		valid = np.logical_and(data["camera"] == camera, np.invert(corrupt_gps))
		corrupt = np.logical_and(data["camera"] == camera, corrupt_gps)

		if len(data[corrupt]) == 0:
			#TODO fix
			continue

		print("Padding %s" % camera)

		# Fit the latitude predictor model
		model, _ = train_model(data, valid, "lat", en.RandomForestRegressor())

		# Predict corrupted latitude data
		data.loc[corrupt, ["lat"]] = model.predict(data.loc[corrupt, ["ts"]])

		# Fit the longitude predictor model
		model, _ = train_model(data, valid, "lon", en.RandomForestRegressor())

		# Predict corrupted longitude data
		data.loc[corrupt, ["lon"]] = model.predict(data.loc[corrupt, ["ts"]])

	# Sort the dataframe again
	data = data.sort_values(["camera", "time"], ignore_index=True)

	# Shave off computation columns and save
	return data[COLUMNS]
