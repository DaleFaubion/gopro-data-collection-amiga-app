#

#

import pandas as pd


def main(f_org, args, df=None):

    # Open the current csv
    label_file = f_org.get_label_file(args.vineyard, args.block, args.date)
    if df is None:
        df = pd.read_csv(label_file, index_col=False)

    print("Predicting Bays")
    return df
