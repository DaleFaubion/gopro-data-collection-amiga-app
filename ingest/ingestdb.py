"""
A module for providing a class to ingest images and meta-data 
into the database
"""

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
		entries = ["image_id", "date", "time", "lat", "lon", "angle", "camera"]
		entries = list(data[entries].to_records(index=False))

		# Add the image metadata to the database
		print("Adding image metadata to the database")
		self.db.add_images(entries)

		return data


	def add_images_to_bays(self, data, vineyard, block):
		"""
		Adds images info to the database
		"""

		# Add the predicted bays
		valid = data[data["pred_bay"].notna()]
		if len(valid) > 0:
			print("Adding predicted bay labels to the database")
			entries = list(valid[["row", "pred_bay", "image_id"]].to_records(index=False))

			self.db.add_images_to_bays(vineyard, block, "true", "pred", entries)

		# Add the real bays (if they exist...)
		valid = data[data["bay"].notna()]

		if len(valid) > 0:
			print("Adding hand-labeled bays to the database")
			
			entries = list(valid[["row", "bay", "image_id"]].to_records(index=False))
			
			self.db.add_images_to_bays(vineyard, block, "true", "true", entries)

		return data


	def add_image_bytes(self, data, image_path, batch_size=64):
		"""
		Add image byte data to the database
		"""

		def loader(image_path):
			with open(image_path, "rb") as f:
				return f.read()

		print("Adding image binaries to the database")

		# Stride through the dataframe
		for chunk_size, chunk in data.groupby(np.arange(len(data)) // batch_size):

			print("chunk %d of %d" % (chunk_size, len(data) // batch_size), end="\r")

			# Get the file names
			if "raw_dir" in chunk.columns:
				file_names = chunk["raw_dir"]

			else:
				file_names = chunk["name"].apply(lambda name: join(image_path, name))

			# Load the files in the chunk
			chunk["binary"] = [loader(f_name) for f_name in file_names]
			entries = list(chunk[["image_id", "binary"]].to_records(index=False))

			# Store the binaries
			self.db.add_image_encodings("jpg", entries)

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
