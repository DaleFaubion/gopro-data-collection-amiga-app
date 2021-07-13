"""
A module for creating the "locations.csv" CSV file containing the 
meta-data about the images along with their path
"""

import os
from os.path import dirname, join, isdir
import pandas as pd
import numpy as np

from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import TAGS, GPSTAGS

from common import COLUMNS

#TODO fix
tag_keys = {}


def get_exif(info, tag):
	"""
	get_exif pulls the value from the exif info, caching the correct key for the tag.
	"""

	if not tag in tag_keys:
		for key, _ in info.items():
			tag_keys[TAGS[key] if key in TAGS else GPSTAGS[key]] = key

	key = tag_keys[tag] if tag in tag_keys else None

	return info[key] if key in info else None


def deg_to_float(value):
	"""
	deg_to_float converts the given latitude or longitude in degrees into a float.

	This function needs to handle datain the format ((d, x), (m, x), (s, x)) or
	(d, m, s).  This is hacky
	"""

	try:
		#TODO fix this
		value = (
			float(value[0][0]) / float(value[0][1]),
			float(value[1][0]) / float(value[1][1]),
			float(value[2][0]) / float(value[2][1]),
		)

	#TODO fix
	except:
		pass

	return value[0] + (value[1] / 60.0) + (value[2] / 3600.0)


def parse_camera(info):
	"""
	parse_camera returns the camera id number from the image metadata.
	"""

	cam = get_exif(info, "BodySerialNumber")

	#TODO fix 
	try:
		return int(cam[1:14])
	except:
		return None


def parse_gps(info):
	"""
	parse_gps parses gps info from the image metadata.
	"""

	info = get_exif(info, "GPSInfo")

	try:
		#TODO fix
		lat, lon = deg_to_float(info[2]), deg_to_float(info[4])
		if info[1] == "S":
			lat *= -1
		if info[3] == "W":
			lon *= -1

	#TODO fix all of this
		return lat, lon
	except:
		return np.nan, np.nan


def parse_time(info):
	"""
	parse_time parses the timestamp from gps metadata.
	"""

	time = get_exif(info, "DateTimeDigitized")

	try:
		return time.split(" ")[1]

	#TODO fix
	except:
		return None


def create_csv(f_org, vineyard, block, date, raw_dir):
	"""
	Creates a pandas dataframe and fills it with the metadata that can be parsed
	from the images.
	"""

	# Get the label file
	label_file = f_org.get_label_file(vineyard, block, date)
	
	if not isdir(dirname(label_file)):
		os.makedirs(dirname(label_file))

	# Create the initial dataframe
	df = pd.DataFrame(columns=COLUMNS)
	idx = 0

	print("Reading Image Metadata")

	# Walk the directory of images
	for root, _, files in os.walk(raw_dir, followlinks=True):
		for image_file in files:
			print("\r", image_file, end=" ")

			# Open the image
			try:
				full_path = join(root, image_file)

				with Image.open(full_path) as img:
					# Do not use the getexif() function instead unless you
					# feel like figuring out the differences and why it happens
					# to cause all the unit tests to fail.
					info = img._getexif()

					# Extract the metadata
					df.loc[idx, "raw_dir"] = full_path
					df.loc[idx, "time"] = parse_time(info)
					df.loc[idx, "camera"] = parse_camera(info)
					df.loc[idx, ["lat", "lon"]] = parse_gps(info)
					df.loc[idx, "focal_length"] = get_exif(info, "FocalLengthIn35mmFilm")
					df.loc[idx, "exposure_time"] = get_exif(info, "ExposureTime")

				idx += 1

			except UnidentifiedImageError:
				print("\rSkipping corrupted file:", full_path)

			#TODO fix
			except Exception as exc:
				print("\rFailed to open", full_path, "with", exc)

	print("\rGenerating CSV				")
	df["vineyard"] = vineyard
	df["block"] = block
	df["date"] = date.replace("-", ":")

	df.to_csv(label_file, index=False)

	return df
