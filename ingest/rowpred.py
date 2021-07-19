"""
A module for predicting the row each image
"""

import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

from ingest.common import to_ord, COLUMNS
from ingest.pred import plot_images


def delta(data, idx, col):
	"""
	delta returns a smoothed gradient of the column.
	"""

	dcol = np.gradient(data.loc[idx, col])
	dcol -= np.median(dcol)

	dcol = np.clip(dcol, -2 * np.std(dcol), 2 * np.std(dcol))
	return np.convolve(dcol, np.ones((4,)) / 4, mode="same")


def rough_clusers(data, idx, dcol, col):
	"""
	rough_clusers returns a column with approximate cluster groupings.
	This will generally return way more clusters than needed which will be corrected
	in subsequent steps
	"""

	row = 1

	# Direction of first entry
	i = idx.index[0]
	p_dx = data.loc[i, dcol] > 0

	dest = data.loc[idx, col].copy()

	for i in idx.index:
		dx = data.loc[i, dcol] > 0

		# Row change
		if dx != p_dx:
			row += 1

		# Mark the row
		dest = row
		p_dx = dx

	return dest

#TODO add more comments
def adjust_clusers(data, idx, col):
	"""
	adjust_clusers reorders the predicted clusters to be in chronological order.
	Assumes that the block is recorded from row 1 onward.
	"""

	clusters = {}
	order = []

	dest = data.loc[idx, col].copy()

	for i in data.loc[idx, col].unique():
		ix = np.logical_and(idx, data[col] == i)
		clusters[i] = np.median(data.loc[ix, ["ts"]])
		order.append(clusters[i])
		dest[ix] = clusters[i]

	order.sort()

	for i in dest.unique():
		ix = np.logical_and(idx, dest == i)
		dest[ix] = order.index(i) + 1

	return dest


#TODO double check this
def predict(data, num_rows):
	"""
	Predicts the row numbers from the ingested gps data.
	"""

	# Generate an ordinal row
	data["ts"] = data["time"].apply(to_ord)
	data["ts"] /= np.max(data["ts"])

	data = data.sort_values(["camera", "ts"], ignore_index=True)

	print("Predicting Rows")

	for cam in data["camera"].dropna().unique():
		idx = data["camera"] == cam

		#TODO why is this?
		# Have the weight the direction of change proportionally to the ts col
		dx = delta(data, idx, "lat")
		dx -= np.min(dx)
		dx /= np.max(dx)
		data.loc[idx, "dlat"] = (dx - 0.5) / 10

		# This is a hacky approximation of clusters
		data.loc[idx, "row"] = rough_clusers(data, idx, "dlat", "row")

		try:
			# TODO switch to DBSCAN
			# Kmeans clustering!
			clusters = KMeans(n_clusters=num_rows)
			data.loc[idx, "row"] = clusters.fit_predict(data.loc[idx, ["ts", "dlat", "row"]])

		#TODO fix
		except Exception as exc:

			print("GPS Data on camera %s too corrupt to predict rows" % cam)
			print(exc)

			#TODO fix this
			continue

		# This reorders the randomly assigned clusters into rows
		#  assumes images are taken in order by row
		data.loc[idx, "row"] = adjust_clusers(data, idx, "row")

	# plot the images by row
	plot_images(data, "predicted_row.png", "row")

	return data[COLUMNS]
