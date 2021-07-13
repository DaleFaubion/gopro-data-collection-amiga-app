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

def pad_cameras(df):
	"""
	pad_cameras fills corrupted camera data with a camera id pulled from another image
	in the same directory.  This could be done better / take into account more than
	just the first image found.
	"""

	camera_dirs = {}

	#TODO lookup what this means (index)
	for idx in df.index:

		dir_name = dirname(df.loc[idx, "raw_dir"])

		if dir_name not in camera_dirs:
			camera_dirs[dir_name] = []

		if dirname(dir_name) not in camera_dirs:
			camera_dirs[dirname(dir_name)] = []

		if df.loc[idx, "camera"] is None or np.isnan(df.loc[idx, "camera"]):
			#TODO fix
			continue

		camera_dirs[dir_name].append(df.loc[idx, "camera"])
		camera_dirs[dirname(dir_name)].append(df.loc[idx, "camera"])

	for dr in camera_dirs:
		camera_dirs[dr] = max(set(camera_dirs[dr]), key=camera_dirs[dr].count)
	
	def get_camera(idx):
		if df.loc[idx, "camera"]:
			#TODO fix multiple returns
			return df.loc[idx, "camera"]

		image_dir = df.loc[idx, "raw_dir"]
		if dirname(image_dir) in camera_dirs:
			#TODO fix multiple returns
			return camera_dirs[dirname(image_dir)]

		return camera_dirs[dirname(dirname(image_dir))]

	return df.index.map(get_camera)


def gps_outliers(df):
	"""
	gps_outliers returns a pandas index of the gps data that is corrupted in the
	dataframe.
	"""

	lat = df["lat"] + df["lon"]

	# GPS data for a given block should be within +- 1 degree of the median,
	#  blocks are very small in terms of coordinates
	return np.logical_or(np.abs(lat - np.median(lat)) > 1, pd.isnull(lat))


def train_model(df, idx, col, model):
	"""
	train_model trains a latitude or longitude prediction model on the non-corrupted
	data.
	"""

	if idx is None:
		features, labels = df[["ts"]], df[col]
	else:
		features, labels = df.loc[idx, ["ts"]], df.loc[idx, col]

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


def predict(f_org, vineyard, block, date, df=None):
	"""
	main interpolates corrupted image metadata in the given date's csv file.
	"""

	# Open the current csv
	label_file = f_org.get_label_file(vineyard, block, date)

	if df is None:
		df = pd.read_csv(label_file, index_col=False)

	print("Padding Camera Metadata")

	# Pads corrupted camera names, assumes that images in a directory will be from
	#  the same camera
	df["camera"] = pad_cameras(df)

	# Pad corrupted time stamps, assumes that images are named chronologically
	df = df.sort_values(["camera", "raw_dir"], ignore_index=True)

	print("Padding Timestamp Metadata")

	# Create time column for k-neighbors
	df["ts"] = df["time"].apply(to_ord)
	df["ts"] = df["ts"].interpolate()
	df["time"] = df["ts"].apply(from_ord)

	print("Padding GPS Metadata")

	# Get the corrupted gps data indices
	corrupt_gps = gps_outliers(df)

	#TODO fix this
	# Correct corrputed latitude / longitude
	for camera in df["camera"].dropna().unique():
		
		# Get the index of valid gps data
		valid = np.logical_and(df["camera"] == camera, np.invert(corrupt_gps))
		corrupt = np.logical_and(df["camera"] == camera, corrupt_gps)

		if len(df[corrupt]) == 0:
			#TODO fix
			continue

		print("Padding %s" % camera)

		# Fit the latitude predictor model
		model, _ = train_model(df, valid, "lat", en.RandomForestRegressor())

		# Predict corrupted latitude data
		df.loc[corrupt, ["lat"]] = model.predict(df.loc[corrupt, ["ts"]])

		# Fit the longitude predictor model
		model, _ = train_model(df, valid, "lon", en.RandomForestRegressor())

		# Predict corrupted longitude data
		df.loc[corrupt, ["lon"]] = model.predict(df.loc[corrupt, ["ts"]])

	# Sort the dataframe again
	df = df.sort_values(["camera", "time"], ignore_index=True)

	# Shave off computation columns and save
	df = df[COLUMNS]
	df.to_csv(label_file, index=False)

	return df
