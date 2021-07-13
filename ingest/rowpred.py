"""
A module for predicting the row each image
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans

from common import to_ord, COLUMNS


def delta(df, idx, col):
	"""
	delta returns a smoothed gradient of the column.
	"""

	dcol = np.gradient(df.loc[idx, col])
	dcol -= np.median(dcol)

	dcol = np.clip(dcol, -2 * np.std(dcol), 2 * np.std(dcol))
	return np.convolve(dcol, np.ones((4,)) / 4, mode="same")


def rough_clusers(df, idx, dcol, col):
	"""
	rough_clusers returns a column with approximate cluster groupings.
	This will generally return way more clusters than needed which will be corrected
	in subsequent steps
	"""

	row = 1

	# Direction of first entry
	i = idx.index[0]
	p_dx = df.loc[i, dcol] > 0

	dest = df.loc[idx, col].copy()

	for i in idx.index:
		dx = df.loc[i, dcol] > 0

		# Row change
		if dx != p_dx:
			row += 1

		# Mark the row
		dest = row
		p_dx = dx

	return dest

#TODO add more comments
def adjust_clusers(df, idx, col):
	"""
	adjust_clusers reorders the predicted clusters to be in chronological order.
	Assumes that the block is recorded from row 1 onward.
	"""

	clusters = {}
	order = []

	dest = df.loc[idx, col].copy()

	for i in df.loc[idx, col].unique():
		ix = np.logical_and(idx, df[col] == i)
		clusters[i] = np.median(df.loc[ix, ["ts"]])
		order.append(clusters[i])
		dest[ix] = clusters[i]

	order.sort()

	for i in dest.unique():
		ix = np.logical_and(idx, dest == i)
		dest[ix] = order.index(i) + 1

	return dest


#TODO double check this
def predict(f_org, vineyard, block, date, rows, df=None):
	"""
	Predicts the row numbers from the ingested gps data.
	"""

	# Open the current csv
	label_file = f_org.get_label_file(vineyard, block, date)

	if df is None:
		df = pd.read_csv(label_file, index_col=False)

	# Generate an ordinal row
	df["ts"] = df["time"].apply(to_ord)
	df["ts"] /= np.max(df["ts"])

	df = df.sort_values(["camera", "ts"], ignore_index=True)

	print("Predicting Rows")

	for cam in df["camera"].dropna().unique():
		idx = df["camera"] == cam

		# Have the weight the direction of change proportionally to the ts col
		dx = delta(df, idx, "lat")
		dx -= np.min(dx)
		dx /= np.max(dx)
		df.loc[idx, "dlat"] = (dx - 0.5) / 10

		# This is a hacky approximation of clusters
		df.loc[idx, "row"] = rough_clusers(df, idx, "dlat", "row")

		try:
			# TODO switch to DBSCAN
			# Kmeans clustering!
			clusters = KMeans(n_clusters=rows)
			df.loc[idx, "row"] = clusters.fit_predict(df.loc[idx, ["ts", "dlat", "row"]])

		#TODO fix
		except:
			print("GPS Data on camera %s too corrupt to predict rows" % cam)

			#TODO fix this
			continue

		# This reorders the randomly assigned clusters into rows
		#  assumes images are taken in order by row
		df.loc[idx, "row"] = adjust_clusers(df, idx, "row")

	df[COLUMNS].to_csv(label_file)

	return df[COLUMNS]
