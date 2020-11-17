# Fall 2020
# Vinetech GPS correction model selection

import __init__
from internal import pad_csv
from internal.common import to_ord
from tests.mocks import file_org as f
import pandas as pd

from sklearn import ensemble

if __name__ == "__main__":
    f_org = f.file_org("v", "b", "2020-01-01", 21, 21, 4)
    df = pd.read_csv(f_org.get_label_file("v", "b", "2019-06-12"))
    df["ts"] = df["time"].apply(to_ord)
    df["ts"] = df["ts"].interpolate()

    print("RandomForestRegressor")
    model, score = pad_csv.train_model(
        df, None, "lat", ensemble.RandomForestRegressor()
    )
    model, score = pad_csv.train_model(
        df, None, "lon", ensemble.RandomForestRegressor()
    )
