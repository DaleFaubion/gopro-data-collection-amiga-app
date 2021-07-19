"""
A module for detecting which camera angle the image was taken
"""

import os

# based on the camera positions on the pole: 1st, 2nd, 3rd
ANGLES = ["1","2","3"]

def find_angle(path):
	"""
	Finds the camera directory in the path which indicate the camera angle
	"""
	# break the path into parts
	parts = path.split(os.sep)	

	# check for each angle
	found = [seg if seg in ANGLES else "" for seg in parts]

	# clear out the parts
	found = [seg for seg in found if seg]

	if found:
		result = found[0]
	else:
		result = ""

	return result


def predict(data):
	"""
	Predicts the camera angle of the images
	"""
	data["angle"] = data["raw_dir"].apply(find_angle)

	return data	
