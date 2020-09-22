# jreamy17@georgefox.edu
# Summer 2019
# VineTech: Data_Preprocessor

if __name__ == "__main__":
    import __init__

from organization import file_org as f_org
from organization import vineyard_layout as vl
from preprocessing.util import *

import pandas as pd
import numpy as np

import argparse
import os

import random

from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier


def arg_parse():
    """
    Function to get arguments from the command line input.
    """

    ap = argparse.ArgumentParser()
    ap.add_argument("-dsp", "--display", action="store_true", help="data to display")
    ap.add_argument(
        "-inf", "--info", action="store_true", help="data to provide information of"
    )
    ap.add_argument(
        "-v", "--vineyard", required=True, help="vineyard of images to display"
    )
    ap.add_argument(
        "-b", "--block", required=True, type=int, help="block of images to display"
    )
    ap.add_argument(
        "-d", "--dates", required=True, nargs="+", help="dates of images to display"
    )
    ap.add_argument("-x", "--x", default="lat", help="column to use for x values")
    ap.add_argument("-y", "--y", default="lon", help="column to use for y values")
    ap.add_argument("-c", "--color", help="column to use for color values")
    ap.add_argument("-s", "--size", help="column or float to use for size")
    ap.add_argument("-cm", "--camera", type=int, help="camera number to view")
    ap.add_argument(
        "-de",
        "--drop_endcaps",
        action="store_true",
        help="whether to remove the endcaps from the data",
    )
    ap.add_argument("-rw", "--rows", type=int, nargs=2, help="range of rows to display")
    ap.add_argument("-by", "--bays", type=int, nargs=2, help="range of bays to display")
    ap.add_argument(
        "-sc", "--scale", action="store_true", help="whether to scale the axis data"
    )
    ap.add_argument(
        "-ss",
        "--std_scale",
        action="store_true",
        help="whether to scale using a standard scaler",
    )

    return vars(ap.parse_args())


class Data_Preprocessor:
    """
    A class used to manipulate and prepare dataframes for machine learning.
    """

    def __init__(self, data, path=None, copy=True):
        """
        Constructs a new Data_reprocessor containing the given dataframe.

        Parameters
        __________
        data : dataframe
            The dataframe to manipulate

        path : String or Path object, optional
            Path to save the dataframe to

        copy : Boolean, default True
            Whether to copy the data to allow resetting
        """

        self.data = data.copy() if copy else data
        self.data_copy = data.copy()
        self.path = path

    @classmethod
    def from_location_and_date(cls, vineyard, block, date):
        """
        Constructs a new Data_Preprocessor containing the dataframe of the
        given vineyard, block, and date.
        """

        label_file = f_org.get_label_file(vineyard, block, date)
        return cls(pd.read_csv(label_file, index_col=[0]), path=label_file)

    @classmethod
    def from_path(cls, path):
        """
        Constructs a new Data_Preprocessor containing the dataframe at the
        given path.
        """

        return cls(pd.read_csv(path, index_col=[0]), path=path)

    ##################
    # Data IO things #
    ##################

    def reload_from_path(self, path):
        """
        Reloads the dataframe from the given path.
        """

        self.path = path
        self.data = pd.read_csv(path, index_col=[0])
        self.data_copy = self.data.copy()

    def copy(self):
        """
        Copies the current Data_Preprocessor.
        """

        data = Data_Preprocessor(self.data)
        data.path = self.path
        return data

    def merge(self, dfP):
        """
        Appends the given Data_Preprocessor to the current one.
        """

        self.data = self.data.append(dfP.get_df(), ignore_index=True)
        self.data = self.data.reset_index(drop=True)

    def set_df(self, df):
        """
        Sets the dataframe of the Data_Preprocessor.
        """

        self.data = df

    def to_csv(self, file_path):
        """
        Saves the dataframe to csv format.
        """

        self.save_df(file_path=file_path)

    def save_df(self, file_path=None):
        """
        Saves the dataframe to csv format.
        """

        # Get the path or raise an error if no path exists
        if file_path is None:
            if self.path is not None:
                path = self.path
            else:
                raise ValueError("Save path not given.")
        else:
            path = file_path

        print("Saving DataFrame to", path)
        self.data.to_csv(path)

    def get_df(self):
        """
        Returns the underlying dataframe.
        """

        return self.data

    def split_df(self, X_cols, y_cols, wrap=False):
        """
        Splits the dataframe, with the option of increasing dimmensionality.
        """

        return split_df(self.data, X_cols, y_cols, wrap=wrap)

    def reset(self):
        """
        Resets the dataframe to the state originally loaded.

        Only stable if `copy = True` at initialization.
        """

        self.data = self.data_copy.copy()

    def disp(self, x, y, size, color, alpha=1.0, title=None, save=True, split_col=None):
        """
        Displays the data using matplotlib.
        """

        if split_col is None:
            title = "locations" if title is None else title
            scatter(self.data, title, x, y, s=size, c=color, alpha=alpha, save=save)
        else:
            # Split data to display
            for val in self.data[split_col].unique():
                v = str(val)
                title = "locations " + v if title is None else title + " " + v
                slice = self.data[split_col] == val
                scatter(
                    self.data[slice],
                    title,
                    x,
                    y,
                    s=size,
                    c=color,
                    alpha=alpha,
                    save=save,
                )

    #####################
    # Column operations #
    #####################

    def reset_index(self):
        """
        Resets the index of the underlying dataframe.
        """

        self.data.reset_index(inplace=True)
        return self.data

    def filter(self, col_name, func):
        """
        Applies a filter to the underlying dataframe.
        """
        """
        Filters a dataframe given the input column and function.
        """

        # Apply a filter function, by column
        locs = list(map(lambda x: func(x), self.data[col_name]))
        self.data = self.data.loc[locs]
        return self.data

    def copy_column(self, col_name, new_name):
        """
        Copies a column of the underlying dataframe.
        """

        self.data[new_name] = self.data[col_name].copy()
        return self.data

    def set(self, row, col, val):
        """
        Sets an element of the underlying dataframe.
        """

        self.data.at[row, col] = val
        return self.data

    def set_col(self, new_name, new_col):
        """
        Sets a column of the underlying dataframe.
        """

        self.data[new_name] = new_col
        return self.data

    def shift_col(self, new_name, col_name, shift):
        """
        Rolls the elements by value in the given column.
        """

        self.data[new_name] = shift_col(self.data, col_name, shift)
        return self.data

    def smooth_column(self, new_name, col_name, dist=5):
        """
        Smoothes local label inaccuracies by comparing to adjacent labels.

        Use for categorical data only (row numbers etc.).  Regression tasks may
        result in near-uniform data.
        """

        self.data[new_name] = smooth_column(self.data, col_name, dist)
        return self.data

    def transform_column(self, new_name, col_name, func):
        """
        Applies the given function to the given column.
        """

        # Apply function
        new_col = self.data[col_name].apply(func)
        self.data[new_name] = new_col
        return self.data

    def subset(self, col_names=[], ranges=[]):
        """
        Selects a subset of the underlying dataframe.
        """

        self.data = subset(self.data, col_names=col_names, ranges=ranges)
        return self.data

    def slide_col(self, new_name, col_name, offset):
        """
        Rolls the elements by row in a given column.
        """

        self.data[new_name] = slide_col(self.data, col_name, offset)
        return self.data

    def delta(self, new_name, col_name, split_cols=[]):
        """
        Applies a differential metric to the given column.

        Allows recursive splitting by elements in split_cols.
        """

        def delta_func(slice, **kwargs):
            return delta(self.data[slice], col_name)

        self.recursive_splitting(delta_func, new_name, split_cols)

    def dist(self, new_name, col_name, x_col, y_col, split_cols=[]):
        """
        Applies a euclidean distance metric to the given column.

        Allows recursive splitting by elements in split_cols.
        """

        def dist_func(slice, **kwargs):
            return dist(self.data, col_name, x_col, y_col)

        self.recursive_splitting(dist_func, new_name, split_cols)

    def slope(self, new_name, x_col, y_col):
        """
        Applies a slope metric to the given columns.
        """

        self.data[new_name] = slope(self.data, x_col, y_col)
        return self.data

    def angle(self, new_name, x_col, y_col, split_cols=[]):
        """
        Applies an angle metric to the given columns.

        Allows recursive splitting by elements in split_cols.
        """

        def angle_func(slice, **kwargs):
            return angle(self.data, x_col, y_col)

        self.recursive_splitting(angle_func, new_name, split_cols)

    def avg(df, new_name, cols, split_cols=[]):
        """
        Applies an average to the given columns.

        Allows recursive splitting by elements in split_cols.
        """

        def avg_func(slice, **kwargs):
            return avg(df, cols)

        self.recursive_splitting(avg_func, new_name, split_cols)

    def round_cols(self, cols_to_round):
        """
        Rounds the given columns.
        """

        self.data = round_cols(self.data, cols_to_round)
        return self.data

    def ordinal_encode(self, cols_to_encode, split_cols=[]):
        """
        Ordinal encodes the given columns.

        Allows recursive splitting by elements in split_cols.
        """

        def ord_encode_func(slice, **kwargs):
            col = ordinal_encode(self.data.loc[slice], cols_to_encode)
            return col[cols_to_encode]

        self.recursive_splitting(ord_encode_func, cols_to_encode, split_cols)
        return self.data

    def range_scale(self, cols_to_scale, range=(0, 1), split_cols=[]):
        """
        Scales the given columns to the given range.

        Allows recursive splitting by elements in split_cols.
        """

        def range_scale_func(slice, **kwargs):
            # Fit MinMax Scaler
            cols = self.data[cols_to_scale].values.reshape(-1, len(cols_to_scale))
            scl = MinMaxScaler(feature_range=range)
            scl.fit(cols)

            # Apply MinMax Scaler
            trns_cols = scl.transform(cols)

            self.data[cols_to_scale] = trns_cols

        self.recursive_splitting(range_scale_func, cols_to_scale, split_cols)
        return self.data

    def std_scale(self, cols_to_scale, split_cols=[]):
        """
        Scales the given columns to a normal distribution.

        Allows recursive splitting by elements in split_cols.
        """

        def std_scale_func(slice, **kwargs):
            col = std_scale(self.data.loc[slice], cols_to_scale)
            return col[cols_to_scale]

        self.recursive_splitting(std_scale_func, cols_to_scale, split_cols)
        return self.data

    def get_std_outliers(self, col_name, cutoff=5, center=False):
        """
        Returns an array containing the outliers of the given column.
        """

        return get_std_outliers(self.data, col_name, cutoff=cutoff, center=center)

    def remove_std_outliers(self, col_name, cutoff=5, split_cols=[]):
        """
        Replaces the outliers of a given column with the average of the
        adjacent values.

        Allows recursive splitting by elements in split_cols
        """

        def std_func(slice, **kwargs):
            col = remove_std_outliers(self.data.loc[slice], col_name, cutoff=cutoff)
            return col[col_name]

        self.recursive_splitting(std_func, col_name, split_cols)
        return self.data

    ####################
    # Generator things #
    ####################

    def add_to_generator(self):
        """
        For use as a generator, stores the current dataframe state.
        """

        self.generator.append(self.data.copy())

    def reset_generator(self):
        """
        For use as a generator, clears the currently held dataframes.
        """

        self.generator = []
        self.gen_loc = 0

    def next_from_generator(self):
        """
        For use as a generator, returns the next held state.
        """

        self.gen_loc = (self.gen_loc + 1) % len(self.generator)
        self.data = self.generator[self.gen_loc]
        return self.data

    #######################
    # Recursive splitting #
    #######################

    def recursive_splitting(
        self, func, new_name, split_cols, vals=[], current=0, filter=None
    ):
        """
        Recursive Splitting function to allow other functions to be applied
        to sections of the underlying dataframe.

        Applies the given function to every permutation of the elements found
        in the given columns.

        Functions applied are expected to accept a filter for the dataframe and
        `kwargs` containing the current permutation of column elements.  Must
        return the column data to be stored in new_col, or `None` signifying
        that it modified the internal state.
        """

        # Get the default filter (all True) if None passed
        filter = pd.Series(True, self.data.index) if filter is None else filter

        # Base case, apply function to slice
        if current == len(split_cols):
            # Get the key-word arguments for function
            kwargs = {}
            for key, val in zip(split_cols, vals):
                kwargs[key] = val

            # Function call and storing data
            new_col = func(filter, **kwargs)
            if not new_col is None and not new_name is None:
                self.data.loc[filter, new_name] = new_col

            # Increment count
            current += 1

        # Recursive case, with tighter filter
        else:
            # Split on column values
            for val in self.data.loc[filter, split_cols[current]].unique():

                def filter_func(x):
                    is_val = self.data.loc[x, split_cols[current]] == val
                    prev_filter = filter.loc[x]
                    return is_val and prev_filter

                # Get new filter and vals
                c_filter = get_filter(self.data, func=filter_func)
                c_vals = vals.copy()
                c_vals.append(val)

                # Recursive call
                self.recursive_splitting(
                    func,
                    new_name,
                    split_cols,
                    vals=c_vals,
                    current=current + 1,
                    filter=c_filter,
                )

    ##########################
    # Location Data Specific #
    ##########################

    def predict_blocks(self, new_name="block", split_cols=["camera"]):
        """
        Uses the average latitude and longitude to predict which vineyard and
        block the dataframe is from.
        """

        def func(slice, **kwargs):
            # Compute averages
            avg_lat = np.average(self.data.loc[slice, ["lat"]])
            avg_lon = np.average(self.data.loc[slice, ["lon"]])

            # Get vineyard and block
            vineyard, block = vl.locate(avg_lat, avg_lon)
            self.data.loc[slice, ["vineyard"]] = vineyard
            self.data.loc[slice, ["block"]] = int(block)

        self.recursive_splitting(func, None, split_cols)

    def predict_rows(
        self,
        new_name="row",
        split_col="angle",
        osc_col="lat",
        X_cols=["lon", "time", "d_lat"],
        iter=500,
        row_range=None,
        fix_cols=["lon", "lat", "d_lat"],
    ):
        """
        Uses a KMeans algorithm to divide the data into rows by longitude,
        time, and the direction of change in the latitude.
        """

        # Used to determine if a chunk of data is enough to constitute
        #  a traversal of the block
        min_pic_scalar = 0.9

        # Copy the current state, which will be restored at the end of the
        #  function call
        save_state = self.data.copy()

        def prep_data():
            """
            Data Prep function for row prediction.
            """

            self.ordinal_encode(["time"], split_cols=[split_col])
            self.delta("d_lat", osc_col)
            self.remove_std_outliers("d_lat", cutoff=5, split_cols=[split_col])
            self.range_scale([osc_col, *X_cols], split_cols=[split_col])

        def clustering_func(slice, vineyard=None, block=None, angle=None):
            """
            KMeans clustering algorithm implementation for row  prediction.
            """

            # Get data that will be used to predict row
            X = self.data.loc[slice, X_cols]

            # Get the vineyard dimensions
            dims = vl.get_vineyard_dimensions(vineyard, block)
            nonlocal row_range
            if row_range is None:
                rows = dims["rows"]
                row_range = [1, rows]
            else:
                rows = row_range[1] - row_range[0] + 1

            min_pics = dims["vines"] * rows * min_pic_scalar
            current_pics = len(self.data[slice])

            # Get the center of the rows
            centers = oscillation_centers(self.data[slice], osc_col, cols=X_cols)

            # print("Predicting", vineyard, block, angle, end="\r")
            if len(X[centers]) > rows and current_pics > min_pics:
                # An initial fix if the centers algorithm returns too many
                #  centers
                print(
                    vineyard,
                    block,
                    angle,
                    "has",
                    len(X[centers]),
                    "centers not",
                    rows,
                    end="\n",
                )
                # print(X[centers].head(len(X[centers])))
                # print(X[centers].info())
                ids = [round((x + 0.5) * current_pics / rows) for x in range(rows)]
                ids = list(map(lambda x: self.data[slice].index[x], ids))
                centers = list(map(lambda x: x in ids, self.data[slice].index))
                print("Fixed centers to have", len(X[centers]))
            if len(X[centers]) != rows:
                # If there is still an incorrect number of centers, add to list
                #  of data to fix
                print(vineyard, block, angle, "has", len(centers), "centers not", rows)
                fix.append((vineyard, block, angle))
            else:
                # Extend centers to include averages
                av_ = 20  # range for averaging
                ind = X[centers].index
                init = pd.DataFrame(columns=X_cols)
                for col in X_cols:
                    init[col] = ind.map(
                        lambda x: np.average(self.data.loc[x - av_ : x + av_, col])
                    )

                # Standard KMeans implementation, row predictions
                alg = KMeans(
                    n_clusters=rows, max_iter=iter, init=init, n_init=1, n_jobs=-1
                )
                rows = alg.fit_predict(X)
                self.data.loc[slice, [new_name]] = rows

                # Renumber groups to be ascending
                new_groups = list(range(row_range[0], row_range[1] + 1))
                renum = renumber_groups(
                    self.data[slice],
                    new_name,
                    "time",
                    descending=False,
                    new_groups=new_groups,
                )
                new_col = transform_column(
                    self.data[slice], new_name, lambda x: renum[x] + 1
                )
                self.data.loc[slice, [new_name]] = new_col

            return self.data.loc[slice][new_name]

        def fix_func(slice, vineyard=None, block=None, angle=None):
            """
            RandomForestClassifier implementation to make row
            predictions on partial data.
            """

            if (vineyard, block, angle) in fix:
                # Fix only the vineyard, block, angle combinations needed
                print(
                    "Estimating", vineyard, block, angle, "with RandomForestClassifier"
                )

                # Data prep
                prep_data()
                train_slice = self.data["row"].notnull()
                test_slice = self.data["row"].isnull()
                X = self.data.loc[train_slice, fix_cols]
                y = self.data.loc[train_slice, "row"].values.reshape(-1,)

                # Train model and predict
                model = RandomForestClassifier(n_estimators=100)
                model.fit(X, y)
                model.predict(X)
                X = self.data.loc[test_slice, fix_cols]
                return model.predict(X)
            else:
                return self.data.loc[slice, "row"]

        # Actual function implementation:
        # Data prep
        prep_data()
        self.data[new_name] = np.NaN

        # Set up lists used
        fix = []
        split_cols = ["vineyard", "block", split_col]

        # Call recursive functions to predict rows on data
        self.recursive_splitting(clustering_func, new_name, split_cols)
        self.recursive_splitting(fix_func, new_name, split_cols)

        # Data cleanup: smooth outliers that pop up mid-row
        self.data[new_name] = smooth_column(self.data, col_name=new_name, dist=5)
        self.data[new_name] = smooth_column(self.data, col_name=new_name, dist=3)
        new_col = smooth_column(self.data, col_name=new_name, dist=1)

        # Restore data state and add the new column
        self.data = save_state
        self.data[new_name] = new_col
        return self.data

    def rand_sub_block(self, rows=None, bays=None, scale=None):
        """
        Pull a random sub-block of the dataframe.
        """

        def rand_range(width, max):
            """
            Sub-function for getting ranges
            """

            remainder = max - width
            start = random.randint(1, remainder + 1)
            return (start, start + width - 1)

        # Get vineyard dimensions
        vineyard = self.data["vineyard"][0]
        block = self.data["block"][0]
        dims = vl.get_vineyard_dimensions(vineyard, block)

        # Get rows and bays
        if not scale is None:
            rows = round(dims["rows"] * scale)
            bays = round(dims["bays"] * scale)
        else:
            rows = dims["rows"] if rows is None else round(rows)
            bays = dims["bays"] if bays is None else round(bays)

        rows = rand_range(rows, dims["rows"])
        bays = rand_range(bays, dims["bays"])

        return self.subset(col_names=["row", "bay"], ranges=[rows, bays])


def main(args):
    """
    Main Function for data visualization, or information display.
    """

    # Data display / visualization mode
    if args["display"]:
        dP = Data_Preprocessor.from_location_and_date(
            args["vineyard"], args["block"], args["dates"][0]
        )

        dP.ordinal_encode(["camera", "time"])

        if args["scale"]:
            dP.range_scale([args["x"], args["y"], args["color"]])
        if args["std_scale"]:
            dP.std_scale([args["x"], args["y"], args["color"]])

        print("displaying data")
        dP.disp(args["x"], args["y"], args["size"], args["color"])

    # Information display mode
    if args["info"]:
        dP = Data_Preprocessor.from_location_and_date(
            args["vineyard"], args["block"], args["dates"][0]
        )
        df = dP.get_df()

        print(df.info())

        if args["rows"] is None:
            print(df.head())
        else:
            print(df[args["rows"][0] : args["rows"][1]])


if __name__ == "__main__":
    args = arg_parse()
    main(args)
