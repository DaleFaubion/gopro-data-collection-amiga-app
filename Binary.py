import re
from argparse import ArgumentParser
from getpass import getpass
from os import walk, mkdir, rmdir, remove, listdir
from os.path import join
from zipfile import ZipFile

import csv
import psycopg2 as pg


def get_binary():
    
    db_name = "vinetech"
    username = "cmeade16"
    password = "fQcm3aPh"
    
    db = pg.connect("host='localhost' dbname='%s' user='%s' password='%s'" % (db_name, username, password))
    cursor = db.cursor()
    sql = "select image_binary from image where image_id = 1"
    cursor.execute(sql)
    image_binary = cursor.fetchone()[0]
    return image_binary

if __name__ == "__main__":

    image_binary = get_binary()
    f = open("verifyFile.jpg", "w")
    f.write(image_binary)
    f.close