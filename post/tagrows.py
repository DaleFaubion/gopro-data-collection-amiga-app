
"""
A Window/CLI program to tag the end of rows then convert those tags into
row predictions
"""

import tkinter as tk
from argparse import ArgumentParser
from csv import reader, writer
from dataclasses import dataclass
from typing import List, Set
from os.path import split

from PIL import Image
from PIL.ImageTk import PhotoImage

DEFAULT_ROW = 1
DEFAULT_BAY = 1
DEFAULT_CAMERA = 1
PATH_IDX = 0

NUM_FIELD_START = 3

WEST = "West"
EAST = "East"

PREFIX = "/srv/projects/vinetech/images/crawford-beck/block09"
REPLACE = "remote"

class ImageViewer:
	def __init__(self, root, date, csv_file):
		self.root = root
		
		self.image_list: List[Image] = []
		self.current_image_index: int = 0
		self.selection: List[Image] = []

		# a list of images that are marked as row endpoints
		self.tags: Set[Image] = set()
		self.date = date

		self.load_images(csv_file)
		self.select_images(DEFAULT_CAMERA)

		self.create_widgets()
		
	def load_images(self, csv_file):
		path_idx = 0
		date_idx = 1

		with open(csv_file) as data:
			for _,row in enumerate(reader(data)):

				local = row[path_idx].replace(PREFIX, REPLACE)
				path = row[path_idx]
				camera = get_camera(path)
				date = row[date_idx]
				time = get_time(path)

				if self.date == date:
					self.image_list.append(ImageMeta(local, path, date, time, camera))

	def select_images(self, camera: int):
		"""
		Picks a subset of the images to display based on the camera, row, and
		bay
		"""
		self.selection = sorted([img for img in self.image_list if img.camera == camera])

	def create_widgets(self):
		self.image_label = tk.Label(self.root)
		self.image_label.pack()
	
		# add button to move the previous image
		self.prev_button = tk.Button(self.root, text='<< Prev', command=lambda: self.shift_image(-1))
		self.prev_button.pack(side=tk.LEFT)

		self.prev_button = tk.Button(self.root, text='<< 10 Prev', command=lambda: self.shift_image(-10))
		self.prev_button.pack(side=tk.LEFT)

		self.prev_button = tk.Button(self.root, text='<< 100 Prev', command=lambda: self.shift_image(-100))
		self.prev_button.pack(side=tk.LEFT)


		# add entries for camera, row, and bay
		self.cam_label = tk.Label(self.root, text="Camera:")
		self.cam_label.pack(side=tk.LEFT)

		self.camera = tk.Entry(self.root)
		self.camera.bind("<Return>", lambda _: self.go_to_image())
		self.camera.pack(side=tk.LEFT)

		self.tag_label = tk.Label(self.root, text="Tag:")
		self.tag_label.pack(side=tk.LEFT)

		self.tag= tk.Entry(self.root)
		self.tag.bind("<Return>", lambda _: self.tag_image())
		self.tag.pack(side=tk.LEFT)

		export = tk.Button(self.root, text="Export", command=self.export)
		export.pack(side=tk.LEFT)
	

		# add button to move the next image
		self.next_button = tk.Button(self.root, text='Next >>', command=lambda: self.shift_image(1))
		self.next_button.pack(side=tk.RIGHT)

		self.next_button = tk.Button(self.root, text='Next 10 >>', command=lambda: self.shift_image(10))
		self.next_button.pack(side=tk.RIGHT)

		self.next_button = tk.Button(self.root, text='Next 100 >>', command=lambda: self.shift_image(100))
		self.next_button.pack(side=tk.RIGHT)

		
		self.show_image()

	def tag_image(self):
		
		tagged = int(self.tag.get())
		current = self.selection[self.current_image_index]

		if tagged:
			if current not in self.tags:
				self.tags.add(current)
		else:
			if current in self.tags:
				self.tags.remove(current)

	def export(self):

		with open(f"fixed-row-pred-{self.date}.csv", "w") as out_file:
			out = writer(out_file)

			out.writerow(["path", "date", "time", "row", "camera", "direction", "post"])

			for camera in [1,2,3,4]:

				# get the camera's images
				self.select_images(camera)

				# sort the tagged images
				tagged = sorted([i.img_time for i in self.tags])

				row_seq = row_iter(camera)

				row, direction = next(row_seq)
				i = 0

				for image in self.selection:
					if image.img_time > tagged[i]:
						try:
							row, direction = next(row_seq)
						except StopIteration:
							pass

						if i < len(tagged) -1:
							i += 1
						
					out.writerow([image.path, image.img_date, image.img_time, row, camera, direction, "0"])
	

	def show_image(self):
	
		image_data = self.selection[self.current_image_index]
		image = Image.open(image_data.local_path)
		image = image.resize((800, 600))

		photo = PhotoImage(image)

		self.image_label.configure(image=photo)
		self.image_label.image = photo
		tagged = image_data in self.tags

		self.root.title(f"{image_data.local_path} Tagged:{tagged} Idx:{self.current_image_index}")

		self.update_entry(self.camera, image_data.camera)
		self.update_entry(self.tag, int(image_data in self.tags))

	def update_entry(self, entry, value):
		"""
		Clears and sets the value in the entry
		"""
		entry.delete(0, tk.END)
		entry.insert(0, str(value))

	def go_to_image(self):
		"""
		Jump to the image specified by camera, starting at the begining
		"""
	
		# get the specified entry
		camera = int(self.camera.get())

		# select the images
		self.select_images(camera)

		try:
			# lookup the new index
			self.current_image_index = [i for i, img in enumerate(self.selection)][0]
		except IndexError as err:
			print(err)
			self.current_image_index = 0
		
		self.show_image()
		
	def shift_image(self, count):
		"""
		Moves by the 'count' amount in image sequence
		"""
		self.current_image_index += count

		# ensure the index is still in bounds
		if self.current_image_index < 0:
			self.current_image_index = 0
		
		elif self.current_image_index >= len(self.selection):
			self.current_image_index = len(self.selection) - 1

		self.show_image()

def row_iter(camera: int):

	if camera in [1,2]:
		row = 1
		direction = EAST
		end = 21
	else:
		row = 0
		direction = WEST
		end = 22
	
	while row <= end:
		yield row, direction

		direction = EAST if direction == WEST else WEST

		if camera in [3,4]:
			row += 2

		yield row, direction
		
		direction = EAST if direction == WEST else WEST

		if camera in [1,2]:
			row += 2

def get_camera(path: str) -> int:
	patterns = {"/%d/" % i : i for i in range(1,5) }

	for pat, ans in patterns.items():
		if pat in path:
			return ans
	return None

def get_time(path: str) -> (str, str):
	time_idx = 1
	_, file = split(path)
	parts = file.split("_")
	return parts[time_idx]


@dataclass
class ImageMeta:
	local_path: str
	path: str
	img_date: str
	img_time: str
	camera: int

	def __hash__(self):
		return hash(self.path)

	def __lt__(self, other):
		return self.img_time < other.img_time

if __name__ == "__main__":

	parser = ArgumentParser()
	parser.add_argument("date", help="The day to do predictions for")
	parser.add_argument("ends_file", help="Predicted ends file")
	args = parser.parse_args()

	root = tk.Tk()
	viewer = ImageViewer(root, args.date, args.ends_file)
	root.mainloop()
