# Fall 2020
# Common functions for ingest scripts

import numpy as np
import time

# columns used in dataframe
columns = [
    "vineyard",
    "block",
    "date",
    "name",
    "time",
    "camera",
    "angle",
    "lat",
    "lon",
    "row",
    "bay",
    "pred_bay",
    "vine_l",
    "vine_r",
    "focal_length",
    "exposure_time",
    "raw_dir",
]


def to_ord(t):
    """
    to_ord converts a time string hh:mm:ss to an integer.
    """

    try:
        t = time.strptime(t, "%H:%M:%S")
        return t.tm_sec + t.tm_min * 60 + t.tm_hour * 3600
    except:
        return np.NaN


def from_ord(t):
    """
    from_ord converts an integer to a time string hh:mm:ss.
    """

    h, m, s = int(t / 3600), int(t / 60) % 60, t % 60
    return "%02d:%02d:%02d" % (h, m, s)
