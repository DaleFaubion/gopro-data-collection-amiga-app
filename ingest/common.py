"""
Common functions for ingest scripts
"""

from time import strptime
import numpy as np

# columns used in dataframe
COLUMNS = [
	"vineyard",
	"block",
	"date",
	"name",
	"time",
	"camera",
	"angle",
	"lat",
	"lon",
	"row",
	"bay",
	"pred_bay",
	"vine_l",
	"vine_r",
	"focal_length",
	"exposure_time",
	"raw_dir",
]


def to_ord(time_str):
	"""
	to_ord converts a time string hh:mm:ss to an integer.
	"""
	try:
		time_obj = strptime(time_str, "%H:%M:%S")
		time_int = time_obj.tm_sec + time_obj.tm_min * 60 + time_obj.tm_hour * 3600
	
	except ValueError:
		time_int = np.NaN

	return time_int


def from_ord(time_num):
	"""
	from_ord converts an integer to a time string hh:mm:ss.
	"""
	hour = int(time_num / 3600)
	minute = int(time_num / 60) % 60
	second = time_num % 60

	return "%02d:%02d:%02d" % (hour, minute, second)
