"""
A module to fix the GPS coordinates and sort image entries
"""

from os.path import dirname
import pandas as pd
import numpy as np

from sklearn.neighbors import KDTree
from sklearn.linear_model import LinearRegression
#from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split
from sklearn import metrics
import matplotlib.pyplot as plt

from ingest.common import COLUMNS, to_ord, from_ord


def plot_images(data, filename):
	"""
	Makes a plot of the images based on lat/long
	"""
	plt.figure(figsize=(10,10))
	plt.scatter(data["lat"], data["lon"], s=5)
	plt.title("Lat/Long of Images")
	plt.savefig(filename)
	plt.close()


#TODO needs a lot more comments
def pad_cameras(data):
	"""
	pad_cameras fills corrupted camera data with a camera id pulled from another image
	in the same directory.  This could be done better / take into account more than
	just the first image found.
	"""

	camera_dirs = {}

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
	THRES = 3.0
	points = pd.DataFrame()

	# normalize the lat and lon dimensions for the sake of numeric
	# stability
	points["lat"] = normalize(data["lat"])
	points["lon"] = normalize(data["lon"])

	# remove the NAN values
	points = points.fillna(0)

	# make the tree
	tree = KDTree(points)

	# check the kernel density (average distance)
	density = tree.kernel_density(points, 1)
	
	# calculate the standard dev
	dev = np.std(np.nan_to_num(density))

	# remove the mean
	density = density - np.mean(density)

	# mark the points more than 3 standard deviations away
	return np.logical_or(np.abs(density) > (dev * THRES), pd.isnull(data["lat"]))


def normalize(array):
	"""
	Normalize the numpy/pandas array
	"""
	return (array - array.mean(skipna=True)) / array.std(skipna=True)


def train_model(data, col, model):
	"""
	train_model trains a latitude or longitude prediction model on the non-corrupted
	data.
	"""
	features = data[["ts"]]
	labels = data[[col]]

	# split into training/testing sets
	x_train, x_test, y_train, y_test = train_test_split(features, labels, test_size=0.2)

	# fit the model to the data
	model.fit(x_train, y_train)

	# Evaluate the model on the test data
	y_pred = model.predict(x_test)

	score = 1 - metrics.mean_absolute_error(y_test, y_pred)

	print("Trained %s model with accuracy: %02.3f" % (col, 100 * score))

	return model


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

	# Create time column for predicting lat and long
	data["ts"] = data["time"].apply(to_ord)
	data["ts"] = data["ts"].interpolate()

	# fill in any missing times
	data["time"] = data["ts"].apply(from_ord)

	print("Padding GPS Metadata")

	# Get the corrupted gps data indices
	corrupt = gps_outliers(data)
	valid =  np.invert(corrupt)

	plot_images(data, "image_loc.png")

	if corrupt.sum() > 0:

		training = data.loc[valid]

		plot_images(data.loc[corrupt], "image_outliers.png")
		plot_images(training, "normal_images.png")

		# Fit the latitude predictor model
		model = train_model(training, "lat", LinearRegression())

		# Predict corrupted latitude data
		data.loc[corrupt, ["lat"]] = model.predict(data.loc[corrupt, ["ts"]])

		# Fit the longitude predictor model
		model = train_model(training, "lon", LinearRegression())

		# Predict corrupted longitude data
		data.loc[corrupt, ["lon"]] = model.predict(data.loc[corrupt, ["ts"]])

		# Sort the dataframe again
		data = data.sort_values(["camera", "time"], ignore_index=True)

		plot_images(data, "image_loc_fixed.png")

	# Shave off computation columns and save
	return data[COLUMNS]
