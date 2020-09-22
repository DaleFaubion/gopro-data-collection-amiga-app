# jreamy17@georgefox.edu
# Fall 2019
# Vinetech bay predictor

if __name__ == "__main__":
    import __init__

from organization import file_org as f_org
from organization import vineyard_layout as vl
from preprocessing.Data_Preprocessor import Data_Preprocessor
from preprocessing import util as u

import pickle
import pandas as pd
import numpy as np

import argparse
import random
import os

from sklearn.metrics import *
from sklearn.ensemble import *

from sklearn.linear_model import *
from sklearn.model_selection import *


def multi_dim_score(y_true, y_pred, mult=True):
    y_true = y_true if isinstance(y_true, np.ndarray) else y_true.values
    y_pred = y_pred if isinstance(y_pred, np.ndarray) else y_pred.values
    y_t = y_true.reshape(-1,)
    y_p = y_pred.reshape(-1,)

    sc = accuracy_score(y_t, y_p)
    return sc * 100 if mult else sc


def prep_dfP(dfP, dims, filter=False):
    if filter:
        dfP.filter("row", lambda x: x <= dims["rows"])
        dfP.filter("bay", lambda x: x > 0 and x <= dims["rows"])
    dfP.transform_column("lat", "lat", lambda x: -x)
    dfP.range_scale(["lat"], range=(1, dims["vines"]), split_cols=["camera", "row"])

    dfP.data = dfP.data.drop(
        [
            "vineyard",
            "block",
            "date",
            "angle",
            "lon",
            "vine_l",
            "vine_r",
            "focal_length",
            "exposure_time",
        ],
        axis=1,
    )

    dfP.transform_column("p_bay", "lat", lambda x: vl.get_bay(x, dims=dims))

    dfP.ordinal_encode(["time"], split_cols=["camera", "row"])
    dfP.range_scale(["time"], split_cols=["camera", "row"])


def split(dfP):
    X_cols = ["lat", "time", "p_bay"]
    y_cols = ["bay"]

    X, y = dfP.split_df(X_cols, y_cols)
    X = X.values.reshape(-1, len(X_cols))
    y = y.values.reshape(-1,)

    return X, y


def get_data(vineyard, block, dates, holdout_rows=None, reset=False, filter=True):
    data_file = os.path.join(
        f_org.get_label_path(vineyard, block, dates), "bay_input_data.csv"
    )

    if reset or not os.path.isfile(data_file):
        dfP = Data_Preprocessor.from_location_and_date(vineyard, block, dates)
        dims = vl.get_vineyard_dimensions(vineyard, block)

        prep_dfP(dfP, dims, filter=filter)
        dfP.to_csv(data_file)
    else:
        dfP = Data_Preprocessor.from_path(data_file)

    if not holdout_rows and filter:
        dfP.filter("row", lambda x: x in holdout_rows)

    return split(dfP)


class Bay_Predictor:
    def __init__(self, name="bay_predictor"):
        # Get old model if it exists

        # Else make new model
        self.model = RandomForestClassifier(n_estimators=100, max_depth=9)
        self.fit = False
        pass

    def train_model(self, dates, holdout_rows=None, vineyard="crawford-beck", block=9):
        # Get the data prepared for training
        X, y = get_data(vineyard, block, dates, holdout_rows=holdout_rows)

        # Begin training the model
        self.model.fit(X, y)
        self.fit = True

    def test_model(self, dates, holdout_rows=None, vineyard="crawford-beck", block=9):
        # Get the data prepared for testing
        X, y = get_data(vineyard, block, dates, holdout_rows=holdout_rows)

        y_pred = self.model.predict(X)

        return multi_dim_score(y_pred, y)

    def save_model(self, name="bay_predictor"):
        with open(os.path.join(f_org.models, name + ".rf"), "wb") as f:
            pickle.dump(self.model, f)

    def load_model(self, name="bay_predictor"):
        # Load the previous model
        with open(os.path.join(f_org.models, name + ".rf"), "rb") as f:
            self.model = pickle.load(f)

    def predict_bays(self, vineyard, block, date, reset=True, filter=False):
        X, y = get_data(vineyard, block, date, reset=reset, filter=filter)
        return self.model.predict(X)


def arg_parse():
    """
    Function to get arguments from the command line input.
    """

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-v", "--vineyard", required=True, help="vineyard of images to display"
    )
    ap.add_argument(
        "-b", "--block", required=True, type=int, help="block of images to display"
    )
    ap.add_argument(
        "-d", "--dates", required=True, nargs="+", help="date of images to display"
    )
    ap.add_argument("-dsp", "--display", action="store_true")
    ap.add_argument("-r", "--reset", action="store_true")

    return vars(ap.parse_args())


if __name__ == "__main__":
    # args = arg_parse()
    vineyard = "crawford-beck"
    block = 9
    date = "2019-06-12"

    bp = Bay_Predictor()

    bp.train_model(
        dates=date, holdout_rows=list(range(15, 22)), vineyard=vineyard, block=block
    )

    score = bp.test_model(
        dates=date, holdout_rows=list(range(15)), vineyard=vineyard, block=block
    )

    print(score)

    bp.predict_bays(vineyard, block, "2019-07-03", reset=False)
