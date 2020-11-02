#


from tests.mocks import file_org as f
from internal import gen_csv, pad_csv, row_pred, bay_pred


class Args:
    pass


args = Args()
args.vineyard = "v"
args.block = "b"
args.date = "2020-01-01"
args.rows = 21

f_org = f.file_org("v", "b", "2020-01-01", rows=21, bays=21, images_per_bay=4)

df = None
# df = gen_csv.main(f_org, args)
# df = pad_csv.main(f_org, args, df=df)
df = row_pred.main(f_org, args, df=df)
df = bay_pred.main(f_org, args, df=df)
