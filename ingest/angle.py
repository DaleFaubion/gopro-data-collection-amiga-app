"""
A module for detecting which camera angle the image was taken
"""

import os

"""
(based on the camera positions on the pole: 1st, 2nd, 3rd)

Existing naming schemes:
	2019: Angle is defined in date folder locations.csv in projects/label folder
	2020: Subfolder structure - 1, 2, 3 (maps to 0, 1, 2, respectively)
	2021: Subfolder structure - Top, Middle, Bottom (same mapping as 2020)
"""
ANGLES = {
	"0": ["0", "1", "top"],
	"1": ["1", "2", "middle"],
	"2": ["2", "3", "bottom"],
}


def find_angle(path):
	"""
	Finds the camera directory in the path which indicate the camera angle
	"""
	# break the path into parts
	parts = path.split(os.sep)

	angle = ""

	for k, v in ANGLES.items():

		# check for each angle
		found = [seg.lower() if seg.lower() in v else "" for seg in parts]

		# clear out the parts
		found = [seg.lower() for seg in found if seg]

		if found:
			angle = k
			break
		else:
			angle = ""
	
	return angle


def predict(data):
	"""
	Predicts the camera angle of the images
	"""
	data["angle"] = data["raw_dir"].apply(find_angle)

	return data
