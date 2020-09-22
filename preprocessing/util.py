# jreamy17@georgefox.edu
# Summer 2019
# VineTech: Preprocessing Utility Functions

if __name__ == "__main__":
    import __init__

from organization import file_org as f_org
from organization import vineyard_layout as vl

import pandas as pd
import numpy as np
import os

from datetime import datetime
import random

import matplotlib
import matplotlib.pyplot as plt

from sklearn.preprocessing import OrdinalEncoder, MinMaxScaler, StandardScaler


def is_number(s):
    """
    Sinple function to check if an object is a number.
    """

    if not s is None:
        try:
            float(s)
            return True
        except ValueError:
            return False


#####################
# Display Functions #
#####################


def save_fig(
    fig_id, folder, tight_layout=True, fig_extension="png", resolution=300, img=None
):

    # Get the image path, ensure it exists
    path = os.path.join(f_org.visual_path, folder)
    if not os.path.isdir(path):
        os.mkdir(path)
    path = os.path.join(path, fig_id + "." + fig_extension)

    # Display layout setup
    if tight_layout:
        plt.tight_layout()

    # Get and save the image
    print("Saving figure", fig_id, "in", folder)
    img = plt if img is None else img
    img.savefig(path, format=fig_extension, dpi=resolution)

    plt.close()


def scatter(data, name, x, y, s=None, c=None, alpha=1.0, save=True):
    # Determine if size is column or number
    if is_number(s):
        size = float(s)
    else:
        size = data[s] / 100 if not s is None else None

    # Convert column 'c' to 0/1 int if boolean
    if type(c) == str:
        if data[c].dtype == np.bool:
            data[c] = data[c].astype(int)

    # Actually draw the scatter plot
    data.plot(
        kind="scatter",
        x=x,
        y=y,
        alpha=alpha,
        s=size,
        label=s,
        figsize=(10, 7),
        c=c,
        cmap=plt.get_cmap("jet"),
        colorbar=True,
        sharex=True,
        title=name,
    )

    # Add legend if needed
    if not s is None:
        plt.legend()

    # Get the image and save it
    img = plt.gcf()
    plt.show()
    if save:
        save_fig(name, x + "_" + y, img=img)


#######################
# DataFrame Functions #
#######################


def split_df(df, X_cols, y_cols, wrap=False):
    """
    For splitting a dataframe with the option of increasing the dimension.

    Useful for creating batches of data.
    """

    # Split the data
    x = df[X_cols]
    y = df[y_cols]

    # Increase the dimensionality for batches
    if wrap:
        x = np.expand_dims(x, axis=0)
        y = np.expand_dims(y, axis=0)
    return (x, y)


def get_filter(df, col_name="index", func=lambda x: x and True):
    """
    For getting a filter of a dataframe by the specified function.
    """

    # Get the filter, by index or column
    if col_name == "index":
        return pd.Series(list(map(lambda x: func(x), df.index)), df.index)
    else:
        return list(map(lambda x: func(x), df[col_name]))


def filter(df, col_name, func):
    """
    Filters a dataframe given the input column and function.
    """

    # Apply a filter function, by column
    locs = list(map(lambda x: func(x), df[col_name]))
    df = df.loc[locs]
    return df


def shift_col(df, col_name, shift, new_name=None):
    """
    Shifts the values of the given column, mod the highest value (value roll).
    """

    df = df.copy()

    # Shift the values by 'shift' input, mod to 'roll' data
    new_col = (df[col_name] + shift) % max(df[col_name])
    df[new_name] = new_col
    return new_col if new_name is None else df


def smooth_column(df, col_name, dist, new_name=None):
    """
    Smoothes local label inaccuracies by comparing to adjacent labels.

    Use for categorical data only (row numbers etc.).  Regression tasks may
    result in near-uniform data.
    """

    df = df.copy()
    new_col = df[col_name].copy()

    # Get range that will be smoothed
    range = df[col_name][dist : len(df) - dist]
    c = df[col_name]
    for i in range.index:
        # If the adjacent values are the same, set to that
        if c[i - dist] == c[i + dist]:
            new_col[i] = c[i - dist]
        # If the value is different from both adjacent, set to min
        #  (fixes endcap predictions)
        elif c[i - dist] != c[i] and c[i] != c[i + dist]:
            new_col[i] = min(c[i - dist], c[i + dist])

    df[col_name] = new_col
    return new_col if new_name is None else df


def transform_column(df, col_name, func, new_name=None):
    """
    Performs the function on the given dataframe column.

    Basically pandas `apply` function.
    """

    df = df.copy()

    # Apply function
    new_col = df[col_name].apply(func)
    df[new_name] = new_col
    return new_col if new_name is None else df


def slide_col(df, col_name, offset, new_name=None):
    """
    Shifts the rows of a given column, rolling over the end of the column.
    """

    df = df.copy()

    # Get the column shift offset
    offset = (len(df[col_name]) + offset) % len(df[col_name])
    shift = df[col_name][offset:].reset_index(drop=True)
    new_col = shift.append(df[col_name][:offset], ignore_index=True)

    df[new_name] = new_col
    return new_col if new_name is None else df


def delta(df, col_name, new_name=None):
    """
    Applies a derivative metric to the given column.

    Returns a new column with the average derivative between the previous and
    next element
    """

    df = df.copy()

    # Get the column
    col = df[col_name]
    new_col = col.copy()

    # Apply derivative to most of the data
    e = len(col) - 1
    for i in range(1, len(col) - 1):
        new_col[i] = (col.iat[i + 1] - col.iat[i - 1]) / 2

    # Apply derivative to endpoints
    new_col[0] = (-3 * col.iat[0] + 4 * col.iat[1] - col.iat[2]) / 2
    new_col[e] = (-3 * col.iat[e] + 4 * col.iat[e - 1] - col.iat[e - 2]) / 2

    df[new_name] = new_col
    return new_col if new_name is None else df


def dist(df, x_col, y_col, new_name=None):
    """
    Applies a euclidean distance metric to the given columns.

    Returns a new column with the euclidean distance between the next and
    previous points in the input columns
    """

    df = df.copy()

    # Get difference of x_col and y_col
    dy = delta(df, None, y_col) ** 2
    dx = delta(df, None, x_col) ** 2

    # Get the distance using sqrt(x^2 + y^2)
    new_col = np.sqrt(delta_x + delta_y)

    df[new_name] = new_col
    return new_col if new_name is None else df


def slope(df, x_col, y_col, new_name=None):
    """
    Applies a derivative metric to the given columns.

    Returns a new column with the slope delta_y_col / delta_x_col.
    """

    df = df.copy()

    # Get the difference of x_col and y_col
    dy = delta(df, y_col)
    dx = delta(df, x_col)

    # Get the slope of the data
    slope = dy / dx
    new_col = list(map(lambda x: x if abs(x) < 1e6 else 1e6, slope))

    df[new_name] = new_col
    return new_col if new_name is None else df


def angle(df, x_col, y_col, new_name=None):
    """
    Applies an arctan metric to the given columns.

    Returns a new column with the angle of the change in the x and y columns.
    """

    df = df.copy()

    # Get the difference of x_col and y_col
    dy = delta(df, y_col)
    dx = delta(df, x_col)

    # Get the angle of the data
    new_col = np.arctan2(dy, dx)

    df[new_name] = new_col
    return new_col if new_name is None else df


def avg(df, col_names, new_name=None):
    """
    Returns a new column that is the average of the other columns.
    """

    df = df.copy()

    # Compute average
    # TODO: replace with np.average if possible
    div = len(col_names)
    avg = df[col_names.pop()]
    for col in col_names:
        avg += df[col]
    new_col = avg / div

    df[new_name] = new_col
    return new_col if new_name is None else df


def round_cols(df, cols_to_round):
    """
    Rounds all the given columns.
    """

    df = df.copy()
    for col in cols_to_round:
        df[col] = np.round(df[col])

    return df


def ordinal_encode(df, cols_to_encode):
    """
    Encodes the given columns of the dataframe using an OrdinalEncoder.
    """

    df = df.copy()

    # Fit Ordinal Encoder
    cols = df[cols_to_encode].values.reshape(-1, len(cols_to_encode))
    enc = OrdinalEncoder(dtype=int)
    enc.fit(cols)

    # Apply Ordinal Encoder
    trns_cols = enc.transform(cols)

    df[cols_to_encode] = trns_cols
    return df


def range_scale(df, cols_to_scale, range=(0, 1)):
    """
    Scales the given columns of the dataframe using a MinMaxScaler.
    """

    df = df.copy()

    # Fit MinMax Scaler
    cols = df[cols_to_scale].values.reshape(-1, len(cols_to_scale))
    scl = MinMaxScaler(feature_range=range)
    scl.fit(cols)

    # Apply MinMax Scaler
    trns_cols = scl.transform(cols)

    df[cols_to_scale] = trns_cols
    return df


def std_scale(df, cols_to_scale):
    """
    Scales the given columns of the dataframe using a StandardScaler.
    """

    df = df.copy()

    # Fit Standard Scaler
    cols = df[cols_to_scale].values.reshape(-1, len(cols_to_scale))
    scl = StandardScaler()
    scl.fit(cols)

    # Apply Standard Scaler
    trns_cols = scl.transform(cols)

    df[cols_to_scale] = trns_cols
    return df


def get_std_outliers(df, colname, cutoff=5, center=False):
    """
    Returns an array containing booleans indicating if elements are outliers.

    Counts np.NaN values as outliers.
    """

    df = df.copy()

    # Fit Standard Scaler
    col = df[colname].values.reshape(-1, 1)
    scl = StandardScaler()
    if center:
        quart = round(len(col) / 4)
        scl.fit(col[quart : 3 * quart, :])
    else:
        scl.fit(col)

    # Apply Standard Scaler
    trns_col = scl.transform(col).reshape(-1,)

    # Return mapping to True if outlier
    return np.array(list(map(lambda x: abs(x) > cutoff or np.isnan(x), trns_col)))


def remove_std_outliers(df, colname, cutoff=5):
    """
    Replaces outliers with the average of their adjacent values.

    Uses `get_std_outliers` to location outliers.
    """

    df = df.copy()

    # Get outliers
    trns_col = get_std_outliers(df, colname, cutoff=cutoff)
    ind = df.index

    # Iterate over the outliers
    for row in range(len(trns_col)):
        if trns_col[row]:
            # First row
            if row == 0:
                # Find next non-outlier
                fore = 1
                while trns_col[row + fore] and row + fore < len(df) - 1:
                    fore += 1

                # Replace with non-outlier
                next = df.loc[ind[row + fore], [colname]]
                df.loc[ind[row], [colname]] = next

            # Last row
            elif row >= len(df) - 1:
                # Find last non-outlier
                back = 1
                while trns_col[row - back] and row - back > 1:
                    back += 1

                # Replace with non-outlier
                prev = df.loc[ind[row - back], [colname]]
                df.loc[ind[row], [colname]] = prev

            # Middle rows
            else:
                # Find next and last non-outliers
                back = 1
                while trns_col[row - back] and row - back > 1:
                    back += 1
                fore = 1
                while trns_col[row + fore] and row + fore < len(df) - 1:
                    fore += 1

                # Replace with average of non-outliers
                prev = df.loc[ind[row - back], [colname]]
                next = df.loc[ind[row + fore], [colname]]
                df.loc[ind[row], [colname]] = (next + prev) / 2
    return df


def subset(df, col_names=[], ranges=[]):
    """
    For getting a subset of a dataframe.
    """

    df = df.copy()

    # Select ranges
    for col, range in zip(col_names, ranges):
        df = df.loc[df[col] >= range[0]]
        df = df.loc[df[col] <= range[1]]

    return df


def renumber_groups(df, group_col, metric_col, descending=False, new_groups=None):
    """
    Sorts labels in group_col by values in the metric_col.

    Returns a dictionary containing the original labels, and their
    corresponding index.
    """

    df = df.copy()

    # Set up output data
    groups = {}
    centers = []

    # Calculate and store centers
    for group in df[group_col].unique():
        center = np.average(df.loc[df[group_col] == group, [metric_col]])
        groups[group] = center
        centers.append(center)

    # Compute label orders
    centers.sort(reverse=descending)
    for group in groups:
        g_idx = centers.index(groups[group])

        # Use supplied new group labels or leave as raw index
        if new_groups is not None:
            g_idx = new_groups[g_idx] - 1

        groups[group] = g_idx

    return groups


def oscillation_centers(df, col_name, cols=None):
    """
    Gets the oscillation centers of a column.
    """

    # Computation setup
    centers = pd.Series(index=df[col_name].index)
    i = df.index[0]
    avg = np.average(df[col_name])
    prev = df.loc[i, col_name] < avg

    print(prev)

    # Label when the data crosses the average
    for i in df.index:
        current = df.loc[i, col_name] < avg
        centers[i] = (current != prev) and not np.isnan(df.loc[i, col_name])
        prev = current

    return centers
