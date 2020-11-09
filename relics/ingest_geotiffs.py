# jreamy17@georgefox.edu
# Summer 2019
# VineTech: Ingest Geotiffs

from __future__ import division, print_function

if __name__ == "__main__":
    import __init__

from organization import file_org as f_org
from organization import vineyard_layout as vl

import pandas as pd
import numpy as np

import argparse
import os

import matplotlib.pyplot as plt
from shutil import copyfile

import gdal
from skimage.transform import ProjectiveTransform

rename = False
disp = True

def is_tiff(filename):
    return filename[len(filename)-4:] == "tiff"

def strip_filename(filename):
    chunks = filename.split("_")

    b_chunk = 0
    while (not "b." in chunks[b_chunk] and b_chunk < len(chunks)):
        b_chunk += 1

    vineyard = "-".join(chunks[3:b_chunk])
    block = int(chunks[b_chunk].split("-")[1][2:])
    date = chunks[0]

    return vineyard, block, date


if __name__ == "__main__":
    gtiff_path = f_org.gtiff_path
    in_path = f_org.ensure_path(os.path.join(gtiff_path, "Ingest"))


    for img in list(filter(lambda f: is_tiff(f), os.listdir(in_path))):
        vineyard, block, date = strip_filename(img)
        print("Ingesting:", vineyard, date, end='\r')
        dims = vl.get_vineyard_dimensions(vineyard, block)
        rows = dims["rows"]
        vines = dims["vines"]

        df_name  = date + "_dataframe.csv"
        tf_name  = date + "_geotiff.tiff"
        geo_path = f_org.ensure_path(os.path.join(gtiff_path, "Data", vineyard))
        df_path  = f_org.ensure_path(os.path.join(geo_path, "block_" + str(block)))
        df_file  = os.path.join(df_path, df_name)
        img_file = os.path.join(df_path, tf_name)

        ds = gdal.Open(os.path.join(in_path, img))

        arr = ds.ReadAsArray()
        div = arr.shape[1]
        arr = arr.reshape(-1,)
        geoT = ds.GetGeoTransform()

        print("Converting Tiff to DataFrame", end='\r')
        df = pd.DataFrame(columns=["lat", "lon", "temp"])
        df["temp"] = arr
        df["lon"] = np.round(df.index%div) * geoT[1] + geoT[0]
        df["lat"] = np.round(df.index/div) * geoT[5] + geoT[3]

        print("Computing Projection", end='\r')
        filter = list(map(lambda x: x > 60, df["temp"]))
        df = df.loc[filter]
        df["max"] = df["lat"] + df["lon"]
        df["min"] = df["lat"] - df["lon"]
        df.reset_index(drop=True, inplace=True)

        NE = df["max"].values.argmax()
        NW = df["min"].values.argmax()
        SW = df["max"].values.argmin()
        SE = df["min"].values.argmin()
        corners = [NW, NE, SE, SW]
        corners = list(map(lambda x: [df["lat"][x], df["lon"][x]], corners))

        src = np.asarray(corners)
        dst = np.asarray([[0,0], [rows,0], [rows,vines], [0,vines]])
        t = ProjectiveTransform()
        if not t.estimate(src, dst):
            print("Invalid Tiff format: lat/lon not convex", img)
            break

        print("Saving data to", df_name, end='\r')
        rv = t(df[["lat", "lon"]])
        df["row"] = rv[:, 0]
        df["vine"] = rv[:, 1]
        df = df.drop("max", axis=1)
        df = df.drop("min", axis=1)

        df.to_csv(df_file)

        if disp:
            print("Rendering Display                       ", end='\r')
            plt.figure(figsize=(5,10))
            plt.scatter(df["lon"], df["lat"], c=df["temp"], cmap=plt.cm.jet, s=0.4)
            plt.colorbar()
            plt.show()

        print("Moving tiff file to", tf_name, end='\r')
        if rename:
            os.rename(os.path.join(in_path, img), img_file)
        else:
            copyfile(os.path.join(in_path, img), img_file)

        print("Completed", vineyard, date, "          ")
