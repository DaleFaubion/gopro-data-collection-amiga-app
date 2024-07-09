
"""
A Window/CLI program to view and verify the predicted rows/bays in the
bay predictions CSV file rover data i.e. 4 cameras
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image
from PIL.ImageTk import PhotoImage
from argparse import ArgumentParser
from csv import reader
from dataclasses import dataclass
from typing import List

DEFAULT_ROW = 1
DEFAULT_BAY = 1
DEFAULT_CAMERA = 1
PATH_IDX = 0
WEST = "West"
EAST = "East"

NUM_FIELD_START = 3
SHORT_FIELDS = 7

PREFIX = "/srv/projects/vinetech/images/crawford-beck/block09"
REPLACE = "remote"

class ImageViewer:
	def __init__(self, root, csv_file):
		self.root = root
		
		self.image_list: List[Image] = []
		self.current_image_index: int = 0
		self.selection: List[Image] = []

		self.load_images(csv_file)
		self.select_images(DEFAULT_CAMERA)

		self.create_widgets()
		
	def load_images(self, csv_file):
		with open(csv_file) as data:
			# skip the header and load all the image metadata
			for i,row in enumerate(reader(data)):
				if i > 1:
					# the row should be in the order: 
					# path, date, time, row, bay, direction
					first = row[:NUM_FIELD_START]
					second = [int(f) for f in row[NUM_FIELD_START:]]

					first[PATH_IDX] = first[PATH_IDX].replace(PREFIX, REPLACE)

					if len(row) == SHORT_FIELDS:
						row.append(0)

					self.image_list.append(ImageMeta(*(first + second)))

	def select_images(self, camera: int):
		"""
		Picks a subset of the images to display based on the camera, row, and
		bay
		"""
		self.selection = [img for img in self.image_list if img.camera == camera]

	def create_widgets(self):
		self.image_label = tk.Label(self.root)
		self.image_label.pack()
	
		# add button to move the previous image
		self.prev_button = tk.Button(self.root, text='<< Prev', command=self.show_prev_image)
		self.prev_button.pack(side=tk.LEFT)

		# add entries for camera, row, and bay
		# camera entry
		self.cam_label = tk.Label(self.root, text="Camera:")
		self.cam_label.pack(side=tk.LEFT)

		self.camera = tk.Entry(self.root)
		self.camera.bind("<Return>", lambda _: self.go_to_image())
		self.camera.pack(side=tk.LEFT)


		# row entry
		self.row_label = tk.Label(self.root, text="Row:")
		self.row_label.pack(side=tk.LEFT)

		self.row = tk.Entry(self.root)
		self.row.bind("<Return>", lambda _: self.go_to_image())
		self.row.pack(side=tk.LEFT)


		# bay entry
		self.bay_label = tk.Label(self.root, text="Bay:")
		self.bay_label.pack(side=tk.LEFT)

		self.bay= tk.Entry(self.root)
		self.bay.bind("<Return>", lambda _: self.go_to_image())
		self.bay.pack(side=tk.LEFT)


		# direction entry
		self.dir_label = tk.Label(self.root, text="Direction:")
		self.dir_label.pack(side=tk.LEFT)
		self.combo = ttk.Combobox(root, values=["East", "West"])
		self.combo.pack(side=tk.LEFT)


		# jump to the image in specified by entry boxes	
		self.jump_button = tk.Button(self.root, text="Go-To", command=self.go_to_image)
		self.jump_button.pack(side=tk.LEFT)
		
		# add button to move the next image
		self.next_button = tk.Button(self.root, text='Next >>', command=self.show_next_image)
		self.next_button.pack(side=tk.LEFT)
		
		self.show_image()
		
	def show_image(self):
	
		image_data = self.selection[self.current_image_index]
		image = Image.open(image_data.path)
		image = image.resize((800, 600))
		has_post = image_data.post == 1

		photo = PhotoImage(image)

		self.image_label.configure(image=photo)
		self.image_label.image = photo

		self.root.title(f"{image_data.path} has post: {has_post}")

		self.update_entry(self.camera, image_data.camera)
		self.update_entry(self.row, image_data.row)
		self.update_entry(self.bay, image_data.bay)
		self.update_entry(self.combo, WEST if image_data.west_dir else EAST)

	def update_entry(self, entry, value):
		"""
		Clears and sets the value in the entry
		"""
		entry.delete(0, tk.END)
		entry.insert(0, str(value))

	def go_to_image(self):
		"""
		Jump to the image specified by camera, row, and bay entries
		"""
	
		# get the specified entry
		camera = int(self.camera.get())
		row = int(self.row.get())
		bay = int(self.bay.get())
		direction = self.combo.get() == WEST

		# select the images
		self.select_images(camera)

		try:
			# lookup the new index
			self.current_image_index = [i for i, img in enumerate(self.selection) 	
				if img.row == row and img.bay == bay and img.west_dir == direction][0]
		except IndexError:
			self.current_image_index = 0
		
		self.show_image()
		

	def show_prev_image(self):
		self.current_image_index -= 1
		if self.current_image_index < 0:
			self.current_image_index = len(self.selection) - 1
		self.show_image()
		
	def show_next_image(self):
		self.current_image_index += 1
		if self.current_image_index >= len(self.selection):
			self.current_image_index = 0
		self.show_image()


@dataclass
class ImageMeta:
	path: str
	img_date: str
	img_time: str
	camera: int
	row: int
	bay: int
	west_dir: bool
	post: bool


if __name__ == "__main__":

	parser = ArgumentParser()
	parser.add_argument("bay_pred", help="Bay prediction CSV file")
	args = parser.parse_args()

	root = tk.Tk()
	viewer = ImageViewer(root, args.bay_pred)
	root.mainloop()
