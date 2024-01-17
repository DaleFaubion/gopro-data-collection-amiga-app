"""
A module for providing a class to ingest images and meta-data 
into the database
"""

from PIL import Image
from io import BytesIO
import torchvision.transforms as T

import numpy as np
import pandas as pd
import itertools as it
import uuid
from os.path import join


class Ingester:
	"""
	A class to ingest images and meta-data into a database
	"""

	def __init__(self, db):
		"""
		Initialize the ingester
		"""
		self.db = db


	def add_uuids(self, data):
		"""
		Add UUIDs to a dataframe
		"""

		# Fill in any missing image column data
		if not "image_id" in data.columns:
			print("Adding a uuid to each image")
			data["image_id"] = [str(uuid.uuid4()) for _ in data.index]

		else:
			print("Filling in any missing uuids")
			missing = data[data["image_id"].isnull()].index
			data.loc[missing, "image_id"] = [str(uuid.uuid4()) for _ in missing]

		return data


	def add_bays(self, data, vineyard, block):
		"""
		Add bays to the database
		"""
		
		# Ensure all the database bays exist
		bays = data["bay"].dropna().unique()
		pred_bays = data["pred_bay"].dropna().unique()
		bays = set((*set(bays), *set(pred_bays)))
		rows = data["row"].dropna().unique()
		all_bays = list(it.product(rows, bays))

		# Add the row/bay pairs to the db
		print("Adding all row/bay pairs to the database")
		self.db.add_bays(vineyard, block, all_bays)

		return data


	def add_metadata(self, data):
		"""
		Add image meta-data to the database
		"""
		# Get the image data that is to be loaded
		fields = ["image_id", "date", "time", "file_name", "orient_id"]
		entries = [tuple(r) for r in data[fields].to_records(index=False)]

		# Add the image metadata to the database
		print("Adding image metadata to the database")
		self.db.add_images(fields, entries)

		return data


	def add_images_to_bays(self, data, vineyard, block):
		"""
		Adds images info to the database
		"""

		# Add the predicted bays
		print("Adding predicted bay labels to the database")
		entries = [tuple(r) for r in 
			data[["row", "bay", "image_id"]].to_records(index=False)]

		self.db.add_images_to_bays(vineyard, block, "pred", "pred", entries)

		return data


	def add_image_bytes(self, data, resize_dims=None, batch_size=64):
		"""
		Add image byte data to the database
		"""

		encoding_name = "jpg"

		# Set the encoding type to resized if there are resize dimensions
		if resize_dims is not None:
			encoding_name = "jpg_resized"

		def resize_loader(image_path: str, dims):
			# Input: path to a file
			# Output: raw JPEG bytes, but they will be shrunk.

			out = BytesIO()

			# Read in file
			img = Image.open(image_path)

			# Create the transformer closure
			# Note, we take in WxH, the more typical human-readable format
			# here we need to give the dimensions as HxW for PyTorch. Invert
			# the tuple
			transformer = T.Compose([
				T.Resize(dims[::-1])
			])

			shrunk_img = transformer(img)

			# Write to memory as "JPEG file"
			shrunk_img.save(out, format="jpeg")

			# Reset internal "file pointer" to beginning for
			# a subsequent read
			out.seek(0)

			# Close old ptrs
			img.close()
			shrunk_img.close()

			# Return bytes
			return out.read()

		def loader(image_path):
			# Input: path to file
			# Output: the raw JPEG bytes of the file
			with open(image_path, "rb") as f:
				return f.read()

		print("Adding image binaries to the database")

		# Stride through the dataframe
		for chunk_size, chunk in data.groupby(np.arange(len(data)) // batch_size):

			print("- Chunk %d of %d" % (chunk_size, len(data) // batch_size), end="\r")

			# Get the file names
			file_names = chunk["file_name"]

			if resize_dims is not None:
				# Load the files in the chunk
				chunk["binary"] = [resize_loader(f_name, resize_dims) for f_name in file_names]
			else:
				chunk["binary"] = [loader(f_name) for f_name in file_names]

			entries = list(chunk[["image_id", "binary"]].to_records(index=False))

			# Store the binaries
			self.db.add_image_encodings(encoding_name, entries)

		return data


	def add_harvest_data(self, harvest_data, vineyard, block, date):
		"""
		Adds harvest data (weights) to the database
		"""

		print("Adding harvest weights to the database")

		columns = ["row_num", "bay_num", "bay_net_kg"]

		h_data = harvest_data.dropna(subset=columns)

		entries = list(h_data[columns].to_records(index=False))

		self.db.add_weights(vineyard, block, date[:4], entries)
