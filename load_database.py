"""
Loads the vinetech image database
"""

import re
from argparse import ArgumentParser
from getpass import getpass
from os import walk, mkdir, rmdir, remove, listdir
from os.path import join
from zipfile import ZipFile

import csv
import psycopg2 as pg


def main(data_dir, db_name, db_user, db_password):
    """
    Runs the database loading program
    """
    errors = 0

    OUT_DIR = "tmp"

    # make a directory
    mkdir(OUT_DIR)

    # connect to the database
    db = connect(db_name, db_user, db_password)

    # get the next bay id
    bay_id = next_bay_id(db)
    MAX_BAY_NUM = 21
    MAX_ROW_NUM = 21

    # generate the bays
    for i in range(1, MAX_ROW_NUM+1):
        for j in range(1, MAX_BAY_NUM+1):
            bay_id = next_bay_id()
            insert_bay(db, bay_id, j, i, 9, "Crawford-Beck")

    # for each year, add all the images
    for root, dirs, files in walk(data_dir):

        # for each csv file in the directory, add images
        for csv_file in files:

            # make sure the file is a csv file
            if csv_file.endswith("locations.csv"):

                csv = read_csv_file(csv_file)

                for image_data in csv:

                    row_num = image_data[10]
                    bay_num = image_data[11]

                    # Only retain images that have bay/row numbers in range [1,21]
                    if (row_num > 0 and row_num < 22) and (bay_num > 0 and bay_num < 22):

                        vineyard_id = image_data[1]
                        block_num = image_data[2]

                        bay_id = get_bay_id(db, bay_num, row_num, block_num, vineyard_id)

                        date = image_data[3]
                        lat = image_data[8]
                        long = image_data[9]
                        image_file_name = image_data[4]

                        image_id = next_image_id()

                        # determine the correct path
                        base_path = '/srv/projects/vinetech/images/crawford-beck/block09'
                        image_directory = image_file_name.split('_')[0]
                        filename = join(base_path, image_directory, image_file_name)

                        # get the file binary
                        with open(filename, mode='rb') as file:
                            image_binary = file.read()

                        # insert an image for the csv line
                        insert_image(db, image_id, bay_id, date, lat, long, image_binary)

    # remove the directory
    rmdir(OUT_DIR)

    # commit the changes
    db.commit()

def connect(db_name, username, password):
    """
    Connects to the postgres database
    """
    return pg.connect("host='localhost' dbname='%s' user='%s' password='%s'" % (db_name, username, password))


def insert_bay(db, bay_id, bay_num, row_num, block_num, vineyard_id):
    """
    Inserts a bay in the database
    """
    # create the cursor
    cursor = db.cursor()

    sql = "insert into bay (bay_id, bay_num, row_num, block_num, vineyard_id) values (%s, %s, %s, %s, %s);"

    # execute the statement
    cursor.execute(sql, [bay_id, bay_num, row_num, block_num, vineyard_id])


def insert_image(db, image_id, bay_id, date, lat, long, image_binary):
    """
    Inserts an image into the database
    """
    # create the cursor
    cursor = db.cursor()

    sql = "insert into image (image_id, bay_id, date, lat, long, image_binary) values (%s, %s, %s, %s, %s, %s);"

    # execute the statement
    cursor.execute(sql, [image_id, bay_id, date, lat, long, image_binary])


def next_bay_id(db):
    """
    Returns the next bay id to use
    """
    # make cursor
    cursor = db.cursor()

    # execute the query
    cursor.execute("select max(bay_id) from bay;")

    last_id = cursor.fetchone()[0]

    # if there are no results start at zero
    if last_id is None:
        last_id = 0

    return int(last_id) + 1


def next_image_id(db):
    """
    Returns the next image id to use
    """
    # make cursor
    cursor = db.cursor()

    # execute the query
    cursor.execute("select max(image_id) from image;")

    last_id = cursor.fetchone()[0]

    # if there are no results start at zero
    if last_id is None:
        last_id = 0

    return int(last_id) + 1


def get_bay_id(db, bay_num, row_num, block_num, vineyard_id):
    """
    Returns the next bay id to use
    """
    # make cursor
    cursor = db.cursor()

    sql = "select bay_id from bay where bay_num = ? and row_num = ? and block_num = ? and vineyard_id = ?;" # values (%s, %s, %s, %s);"

    # execute the statement
    cursor.execute(sql, [bay_num, row_num, block_num, vineyard_id])

    bay_id = cursor.fetchone()[0]

    return bay_id


def read_csv_file(csv_file):
    with open(csv_file) as csvfile:
        read_csv = csv.reader(csvfile, delimiter=',')

        # expected indexes:
        # 0: index
        # 1: vineyard_id
        # 2: block_num
        # 3: date
        # 4: image file name
        # 5: time
        # 6: camera id
        # 7: angle
        # 8: lat
        # 9: long
        # 10: row_num
        # 11: bay_num
        # 12: vine_l
        # 13: vine_r
        # 14: focal length
        # 15: exposure time

        array = []

        for row in read_csv:
            array.append(row)

        # array.pop(0)
        # print(array)

        return array


def get_image_binary(image_file_name):
    '''
    /srv/projects/vinetech/images/crawford-beck/block09

    Inside are image directories: YYYY-MM-DD
    Inside image directories: (Image Names as determined above)

    :param image_file_name:
    :return:
    '''

def read_source(file_name):
    """
    Reads the []
    """
    pass


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("-d", default="/srv/projects/vinetech/labels/crawford-beck/", help="The data directory")
    parser.add_argument("-db", default="vinetech", help="The database name to connect to")
    parser.add_argument("-db_user", default="cmeade16", help="The database username")
    parser.add_argument("-password", default="fQcm3aPh", help="The user's password; SECRET: Don't steal... please")

    args = parser.parse_args()

    # prompt the user for a password
    # password = getpass("enter password:")

    main(args.d, args.db, args.db_user, args.password)