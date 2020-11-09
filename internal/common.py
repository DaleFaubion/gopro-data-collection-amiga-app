#

#

import numpy as np
import time

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
    try:
        t = time.strptime(t, "%H:%M:%S")
        return t.tm_sec + t.tm_min * 60 + t.tm_hour * 3600
    except:
        return np.NaN


def from_ord(t):
    h, m, s = int(t / 3600), int(t / 60) % 60, t % 60
    return "%02d:%02d:%02d" % (h, m, s)
