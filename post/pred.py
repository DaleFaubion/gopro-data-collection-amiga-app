
"""
Predicts whether a image has a post in it or not
"""

from argparse import ArgumentParser
from os.path import join
from os import walk
from csv import writer

from PIL import Image, UnidentifiedImageError
import torch as t
import numpy as np

def main(model_path, image_dir, out_path):
	"""
	Runs a trained model on the images found in the given directory and 
	predict if the image contains a post
	"""
	count = 0
	
	# load the model
	print("Loading model")
	model = t.load(model_path)

	# open the csv file
	with open(out_path, "w") as csv_path:

		csv_file = writer(csv_path)

		# for each image file
		for root, _, files in walk(image_dir):

			# for each image file make a prediction
			for img_path in files:

				name = img_path.lower()

				if name.endswith("jpeg") or name.endswith("jpg"):

					try:
						path = join(root, img_path)

						# load the image
						image = Image.open(path)

						# make it into a tensor
						img_tensor = t.tensor(np.array(image), dtype=t.float).permute(2, 0, 1).unsqueeze(0)

						with t.no_grad():
							model.eval()

							# predict if the image has a post
							pred = model(img_tensor.cuda()).cpu().data.numpy().argmax()

							# write the prediction to file
							csv_file.writerow([path, str(pred)])

							count += 1

								
						if count % 1000 == 0:
							print("Processed", count)
					
					except UnidentifiedImageError:
						print("Could not load image:", img_path)



if __name__ == "__main__":

	parser = ArgumentParser()

	parser.add_argument("model_file", help="The file containing the trained model")
	parser.add_argument("image_dir", help="The directory containing image files")
	parser.add_argument("out_file", default="posts.csv", help="The file to write the predicted posts to")

	args = parser.parse_args()


	main(args.model_file, args.image_dir, args.out_file)
