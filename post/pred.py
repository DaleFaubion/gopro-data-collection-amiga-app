
"""
Predicts whether a image has a post in it or not
"""

from argparse import ArgumentParser
from os.path import join
from os import walk
from csv import writer
import re

from PIL.ExifTags import TAGS, GPSTAGS
from PIL import Image, UnidentifiedImageError
import torch as t
import numpy as np
from torchvision.transforms import Resize


#major hack..
tag_keys = {}

def main(model_path, image_dir, out_path, include):
	"""
	Runs a trained model on the images found in the given directory and 
	predict if the image contains a post
	"""
	count = 0
	
	resize = Resize([300, 400], antialias=True)

	# load the model
	print("Loading model")
	model = t.load(model_path)

	# open the csv file
	with open(out_path, "w") as csv_path:

		csv_file = writer(csv_path)

		# for each image file
		for root, _, files in walk(image_dir):

			if include in root:

				# for each image file make a prediction
				for img_path in files:

					name = img_path.lower()

					if name.endswith("jpeg") or name.endswith("jpg"):

						try:
							path = join(root, img_path)

							# load the image
							image = Image.open(path)

							# parse the data (YYYY-MM-DD out of the path
							matches = re.findall(r"[0-9]+-[0-9]+-[0-9]+", path)
							date = matches[0] if matches else None

							# parse out the timestamp info from the exif data
							info = image._getexif()
							timestamp = parse_time(info)

							# make it into a tensor
							img_tensor = t.tensor(np.array(image), dtype=t.float).permute(2, 0, 1)
							img_tensor = resize(img_tensor).unsqueeze(0)

							with t.no_grad():
								model.eval()

								# predict if the image has a post
								pred = model(img_tensor.cuda()).cpu().data.numpy().argmax()

								# write the prediction to file
								csv_file.writerow([path, date, timestamp, str(pred)])

								count += 1

									
							if count % 1000 == 0:
								print("Processed", count)
						
						except UnidentifiedImageError:
							print("Could not load image:", img_path)

# hack... the structure of the project needs to be reworked
def get_exif(info, tag):
	"""
	get_exif pulls the value from the exif info, caching the correct key for the tag.
	"""

	if not tag in tag_keys:
		for key, _ in info.items():
			tag_keys[TAGS[key] if key in TAGS else GPSTAGS[key]] = key

	key = tag_keys[tag] if tag in tag_keys else None

	return info[key] if key in info else None


def parse_time(info):
	"""
	parse_time parses the timestamp from gps metadata.
	"""
	result = None
	time = get_exif(info, "DateTimeDigitized")

	try:
		result = time.split(" ")[1]

	except:
		pass

	return result


if __name__ == "__main__":

	parser = ArgumentParser()

	parser.add_argument("model_file", help="The file containing the trained model")
	parser.add_argument("image_dir", help="The directory containing image files")
	parser.add_argument("out_file", default="posts.csv", help="The file to write the predicted posts to")
	parser.add_argument("-i", default="", help="A path segment to only include")

	args = parser.parse_args()


	main(args.model_file, args.image_dir, args.out_file, args.i)
