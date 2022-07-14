
"""
Module for filtering images based on their GPS data, removing outliers
"""

# the number of standard deviations to be an outlier
OUTLIER_DEV = 6.0

def filter_gps_outliers(data):
	"""
	Filters images based on GPS outliers
	"""
	# filter based on lat
	data = filter_by_col(data, "lat")

	# filter based on lon
	data = filter_by_col(data, "lon")

	return data


def filter_by_col(data, column):
	"""
	Filter the images based on an outlier column
	"""
	# find the average
	avg = data[column].mean()

	# find the standard deviation
	std = data[column].std()

	upper = avg + (OUTLIER_DEV * std)
	lower = avg - (OUTLIER_DEV * std)

	return data[ (data[column] > lower) & (data[column] < upper) ]
