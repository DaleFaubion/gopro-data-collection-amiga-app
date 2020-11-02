# Fall 2020
# Vinetech mock file org

import os
import tempfile
import itertools as it

import pandas as pd
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import exif

# Have to hack in this key to the exif maps to be able to add it to the mock images
exif._app1_metadata.ATTRIBUTE_ID_MAP["body_serial_number"] = 42033
exif._app1_metadata.ATTRIBUTE_TYPE_MAP["body_serial_number"] = (
    int(exif._constants.ExifTypes.ASCII),
    "exif",
)


def mock_locations(rows, bays, img_per_bay=5, corner="SE", variance=0.8, delta=0.3):

    dx, dy = 0, 0
    idx = 0

    # Get the direction of motion based on starting corner
    xdir = -1 if corner[1] == "E" else 1
    ydir = -1 if corner[0] == "N" else 1

    df = pd.DataFrame(
        columns=["row", "bay", "image", "lat", "lon"],
        index=np.arange(rows * bays * img_per_bay),
    )
    for row, bay, img in it.product(range(rows), range(bays), range(img_per_bay)):

        # Simulate walking both directions
        b = bay if (row % 2) ^ (ydir > 0) else (bays - bay - 1)
        i = img if (row % 2) ^ (ydir > 0) else (img_per_bay - img - 1)

        # Enter the data to return
        df.loc[idx, ["row", "bay", "image"]] = (row, b, i)
        df.loc[idx, "lat"] = xdir * (row + dx)
        df.loc[idx, "lon"] = ydir * ((b * img_per_bay + i) / img_per_bay + dy)

        # Update the walking variables
        dx += delta * (np.random.random() - 0.5)
        dy += delta * (np.random.random() - 0.5)
        dx = -variance if dx < -variance else variance if dx > variance else dx
        dy = -variance if dy < -variance else variance if dy > variance else dy
        idx += 1

    df["lat"] -= np.min(df["lat"])
    df["lon"] -= np.min(df["lon"])

    return df


class file_org:
    def __init__(
        self, vineyard, block, date, rows, bays, images_per_bay, data_shape=(3, 3, 3),
    ):
        self.vineyard = vineyard
        self.block = block
        self.date = date
        self.data_shape = data_shape

        self.data_path = "testdata"
        self.data_dir = os.path.join(
            self.data_path, "{}_{}_{}".format(rows, bays, images_per_bay)
        )
        self.image_path = os.path.join(self.data_dir, "images")

        if not os.path.isdir(self.data_dir):
            os.makedirs(self.data_dir)

        if not os.path.isdir(self.image_path):
            os.makedirs(self.image_path)

        self.__gen_images(rows, bays, images_per_bay, images_per_directory=100)
        self.__gen_labels("2019-07-31", rows, bays, images_per_bay)

    def get_image_path(self, vineyard, block, date, norm=None):
        return self.image_path

    def get_label_file(self, vineyard, block, date):
        return os.path.join(self.data_dir, date, "labels.csv")

    def __gen_images(
        self, rows, bays, images_per_bay, images_per_directory, dropout=0.05
    ):
        """
        Creates a directory full of unprocessed images
        """

        h, m, s = 0, 0, 0

        dir_idx = 0
        subdir = 0

        base_path = os.path.join("testdata", "ingest", "raw_images")

        for cam in range(3):

            if not os.path.isdir(os.path.join(base_path, str(cam), str(subdir))):
                os.makedirs(os.path.join(base_path, str(cam), str(subdir)))

            locs = mock_locations(rows, bays, images_per_bay, "SE" if cam % 2 else "NE")
            idx = 0

            for row, bay, img, in it.product(
                range(rows), range(bays), range(images_per_bay)
            ):

                # Mock clock time (inc by 1 second)
                s = (s + 1) % 60
                m = m if s else (m + 1) % 60
                h = h if m or s else (h + 1) % 24

                # Path info
                file_name = "{}_{}_{}.JPG".format(row, bay, img)
                file_path = os.path.join(base_path, str(cam), str(subdir), file_name)

                # Create the image
                if not os.path.isfile(file_path):

                    # Create an image with no metadata
                    data = np.random.randint(
                        0, 255, size=self.data_shape, dtype=np.uint8
                    )
                    image = Image.fromarray(data)
                    image.save(file_path)

                    # Open the image to write metadata
                    with open(file_path, "rb") as f:
                        image = exif.Image(f)

                    # Write gps metadata
                    image.gps_latitude = (123.0, 8.0, locs.loc[idx, "lat"])
                    image.gps_latitude_ref = "N"
                    image.gps_longitude = (45.0, 6.0, locs.loc[idx, "lon"])
                    image.gps_longitude_ref = "W"
                    image.gps_altitude = 2000
                    image.gps_altitude_ref = exif.GpsAltitudeRef.ABOVE_SEA_LEVEL

                    # Write other useful metadata
                    image.datetime_digitized = "2020:01:01 %02d:%02d:%02d" % (h, m, s)
                    image.exposure_time = np.random.random() / 1000
                    image.focal_length_in_35mm_film = 15

                    if np.random.random() > dropout:
                        image.body_serial_number = "C328132817908%d" % cam

                    # Corrupt some of the data
                    if np.random.random() < dropout:
                        image.gps_latitude = (0.0, 0.0, 0.0)
                        image.gps_longitude = (0.0, 0.0, 0.0)

                    # Write the metadata to file
                    with open(file_path, "wb") as f:
                        f.write(image.get_file())

                idx += 1

                # Change subdirectory if needed
                dir_idx += 1
                if dir_idx >= images_per_directory:
                    dir_idx, subdir = 0, subdir + 1
                    if not os.path.isdir(
                        os.path.join(base_path, str(cam), str(subdir))
                    ):
                        os.makedirs(os.path.join(base_path, str(cam), str(subdir)))

    def __gen_labels(self, date, rows, bays, images_per_bay):
        label_file = self.get_label_file(self.vineyard, self.block, date)
        df = mock_locations(rows, bays, images_per_bay).reset_index()
        df["time"] = df.index.map(
            lambda x: "%02d:%02d:%02d" % (int(x / 3600) % 24, int(x / 60) % 60, x % 60)
        )

        df["camera"] = 10

        if not os.path.isdir(os.path.dirname(label_file)):
            os.makedirs(os.path.dirname(label_file))
        df.to_csv(label_file, index=False)
