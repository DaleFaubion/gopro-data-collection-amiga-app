from argparse import ArgumentParser
from itertools import groupby, chain
from csv import reader, writer

TIME = 2
END_POST = 3

# TODO Copied the predrow.py and will update this to match the desired 

def main(ends_file, out_file):
	"""
	Predicts the row based on the "end post" prediction
	"""

	# load the data
	# smooth out suspected false positives
	# group up the images into rows
	# write the rows to a file
	write_rows(out_file, group_rows(smooth_pred(load_data(ends_file))))


def load_data(csv_file):
	"""
    Loads image data from the specified CSV file, converts the 'END_POST' column to integers, 
    and sorts the data by time.

    Args:
        csv_file (str): The path to the CSV file containing image data.

    Returns:
        result (list of lists): A list of image data rows, where each row is represented as a list.
    """
	result = []

	with open(csv_file) as in_file:
		for row in reader(in_file):
			row[END_POST] = int(row[END_POST])
			result.append(row)


	#sort the images by time
	result.sort(key=lambda r: adjust_time(r[TIME]))

	return result


def adjust_time(time_str):
	"""
    Adjusts the given time string to handle 11 PM (hour 23) from the previous night as a negative value
    for proper sorting. This function is a workaround for correcting GOPRO time stamp sorting issues.

    Args:
        time_str (str): A time string in the format "HH:MM:SS" or "23:MM:SS".

    Returns:
        adjusted_time_str (str): The adjusted time string with a negative sign if it starts with "23",
                                 otherwise returns the input time string unchanged.
    """
	if time_str.startswith("23"):
		return "-" + time_str
	else:
		return time_str


def smooth_pred(row_data):
	 """
    Smooths out potential false positives in the given data by examining each entry.
    
    Args:
        row_data (list of lists of tuples): A list of image data rows with predictions.
        
    Returns:
        row_data (list of lists of tuples): The modified input data with potential false positives smoothed out.
    """

	# for each entry, if the predicted end post (1) is surrounded by 0's
	# then make the prediction a zero
	for i in range(1, len(row_data) - 1):

		prev = row_data[i - 1][END_POST] == 0
		adv = row_data[i + 1][END_POST] == 0
		is_end = row_data[i][END_POST] == 1

		# make the current prediction "no post"
		if prev and is_end and adv:
			row_data[i][END_POST] = 0

	return row_data


def group_rows(row_data):
	"""
    Group rows of image data from a CSV file into alternating sequences of "ends" and "no ends" groups,
    and then combine every three consecutive groups into rows.

    Args:
        row_data (list of lists of tuples): A list of image data rows loaded from a CSV file.

    Returns:
        rows (list of lists of tuples): A list of rows where each row is a combination of three consecutive
                                        groups, consisting of "ends", "no ends", and "ends".
    """
	#turns = 0
	#is_turns = False

	# group up the images into rows 
	groups = [list(g) for _, g in groupby(row_data, key=lambda r: r[END_POST])]

	# the groups should go ends, no ends, ends, no ends, ends, ...
	# hence every "ends" group needs to be split in half
	split_groups = []	

	for i, group in enumerate(groups):
		
		# even indexed groups will be "ends"
		# skip the first and last "ends" group
		if i > 0 and i < len(groups) -1 and i % 2 == 0:
			mid = len(group) // 2
			first = group[:mid]
			second = group[mid:]
			split_groups.append(first)
			split_groups.append(second)

		else:
			split_groups.append(group)

	# combine every three i.e. ends, no ends, ends
	rows = []

	for i in range(0, len(split_groups), 3):
		parts = split_groups[i:i + 3]

		rows.append(list(chain(*parts)))

	# print out information about the rows
	for i, row in enumerate(rows):
		print("Row %2d: %d" % (i + 1, len(row)))

	return rows


def write_rows(out_file, rows):
	"""
    Writes all the rows of image data to the specified CSV file, appending row numbers to each image data row.

    Args:
        out_file (str): The path to the CSV file where the image data will be written.
        rows (list of lists of tuples): A list of rows, where each row is a list of image data represented as tuples.

    Returns:
        None
    """

	with open(out_file, "w") as out:
		csv_out = writer(out)

		# for each row in the list of rows, write the row data with the
		# row number appended to the end
		for i, row in enumerate(rows):
		
			# write out each image data
			for img_data in row:
			
				# replace the end post prediction with the row prediction
				img_data[END_POST] = i + 1

				csv_out.writerow(img_data)


if __name__ == "__main__":

	parser = ArgumentParser()

	parser.add_argument("ends_file", help="The row 'ends' prediction CSV file")
	parser.add_argument("out_file", help="The file to write the row predictions to")

	args = parser.parse_args()

	main(args.ends_file, args.out_file)
