from argparse import ArgumentParser
from collections import namedtuple

from PIL import Image
import dhash

from database import Database, BayId

Options = namedtuple("Options", ["vineyard", "block", "db_config", "threshold", "dry_run", "image_type", "angle"])

def main():
	
	# parse commandline args
	parser = ArgumentParser()

	parser.add_argument("dates", nargs="*", help="The dates to apply deduplication to")
	parser.add_argument("-dry", action="store_true", help="Try the deduplication but do not save the results to the db")
	parser.add_argument("-t", type=int, default=5, 
		help="The upper threshold of the number of edits that is considered to mean two images are the same")
	parser.add_argument("-db", default="db_config.ini", help="Database connection configuration file")
	parser.add_argument("-vineyard", default="crawford-beck")
	parser.add_argument("-block", default=9)
	parser.add_argument("-image_type", default="jpg_resized")
	parser.add_argument("-angle", type=int, default=0)


	args = parser.parse_args()

	options = Options(args.vineyard, args.block, args.db, args.t, args.dry, args.image_type, args.angle)

	# for each day, mark duplicates
	for date in args.dates:
		mark_duplicates(options, date)


def mark_duplicates(options:Options, date:str):
	"""
	Goes through the images for the given day and marks any duplicates.
	Note that only one out of a duplicate pair will be marked
	"""
	
	# connect to the database
	db_conn = Database()
	db_conn.connect(options.db_config)

	# get the rows and bayes
	rows = db_conn.get_rows(options.vineyard, options.block)
	bays = db_conn.get_bays(options.vineyard, options.block)

	# for each row, bay combo remove duplciates
	for row in rows:
		for bay in bays:

			# make the bay id
			bay_id = BayId(options.vineyard, options.block, row, bay)

			# get all the images for the bay/date
			images = db_conn.get_images(db_conn.get_image_ids(bay_id, date, options.image_type), options.image_type)

			# make the images into PIL objects
			images = {k: Image.open(b) for k,b in images.items()}

			# make a set of images to remove
			dups = set()

			# check all pairwise combinations
			for i,left in enumerate(images):
				for j,right in enumerate(images):

					# if the pair is a duplicate, mark one of them as a duplciate
					# if the left image is marked as a duplicate that means
					# it was previously a "right" duplicate image
					if i < j and left not in dups:
						
						diff = count_differences(images[left], images[right])

						if diff <= options.threshold:
							print("Row %d, Bay %d, Duplicate: %d -> %s, %s" % (row, bay, diff, left, right))
							dups.add(right)
			
			if not options.dry_run:
				
				# remove all the duplicates
				for image in dups:
					print("Removing %s" % image)
					remove_duplicate(db_conn, image)


def count_differences(left:Image, right:Image) -> int:
	"""
	Returns a count of the differences between the images
	"""
	l_row, l_col = dhash.dhash_row_col(left)
	r_row, r_col = dhash.dhash_row_col(right)

	return dhash.get_num_bits_different(l_row, r_row) + dhash.get_num_bits_different(l_col, r_col)


def remove_duplicate(db_conn, image_id:str):
	"""
	Marks the image as a duplicate
	"""
	sql = "delete from image where image_id = %s"

	db_conn.execute(sql, image_id)


if __name__ == "__main__":
	main()
