from argparse import ArgumentParser
from itertools import groupby, chain
from csv import reader, writer
import re

TIME = 2
END_POST = 3
CAMERA_FINDER_PATTERN = r'/(?P<number>[1-4])/'

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
    Loads the image data from the CSV file
    """
    result = []

    with open(csv_file) as in_file:
        for row in reader(in_file):
            row[END_POST] = int(row[END_POST])
            result.append(row)

    # sort the images by time
    result.sort(key=lambda r: adjust_time(r[TIME]))

    return result


def adjust_time(time_str):
    """
    This is a hack... make 11 PM i.e. hour 23 from the "night" before
    negative so that it sorts properly. The GOPRO time stamps are off
    but are in the correct order for the most part
    """
    if time_str.startswith("23"):
        return "-" + time_str
    else:
        return time_str


def smooth_pred(row_data):
    """
    Smooth out the potential false positives in the data
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
    Group up the image data into rows (list of lists of tuples)
    """

    # group up the images into rows
    groups = [list(g) for _, g in groupby(row_data, key=lambda r: r[END_POST])]

    # the groups should go ends, no ends, ends, no ends, ends, ...
    # hence every "ends" group needs to be split in half
    split_groups = []

    for i, group in enumerate(groups):

        # even indexed groups will be "ends"
        # skip the first and last "ends" group
        if len(groups) - 1 > i > 0 == i % 2:
            mid = len(group) // 2
            first = group[:mid]
            second = group[mid:]
            split_groups.append(first)
            split_groups.append(second)

        else:
            split_groups.append(group)

    # combine every three i.e. ends, no ends, ends
    rows = []
    camera_direction = {1: [0, "West"], 2: [0, "West"],
                        3: [0, "East"], 4: [0, "East"]}

    for i in range(0, len(split_groups), 3):
        parts = split_groups[i:i + 3]

        rows.append(list(chain(*parts)))

        # print out information about the rows

    for each in rows:
        for i, row in enumerate(each):
            camera_num = int(find_camera(row[0]))
            print(camera_num)
            row.append(camera_num)

            # code to switch the bearing on 2 or more successful end post predictions
            # (essentially if the end row in 1)

            camera_direction[camera_num][0] += row[3]
            if camera_direction[camera_num][0] > 1:
                if camera_direction[camera_num][1] == "East":
                    camera_direction[camera_num][1] = "West"
                else:
                    camera_direction[camera_num][1] = "East"
                camera_direction[camera_num][0] = 0

            row.append(camera_direction[camera_num][1])
            print("Row %2d: %d" % (i + 1, len(row)))

    return rows


def write_rows(out_file, rows):
    """
    Write all the rows out to the CSV file
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


def find_camera(metadata):
    """

    """
    pattern = r'/(?P<number>[1-4])/'
    camera_num = re.search(pattern, metadata)['number']

    return camera_num


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("ends_file", help="The row 'ends' prediction CSV file")
    parser.add_argument("out_file", help="The file to write the row predictions to")

    args = parser.parse_args()

    main(args.ends_file, args.out_file)
