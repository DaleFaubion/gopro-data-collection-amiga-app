import unittest


import __init__
from tests.mocks import file_org as f

from internal import gen_csv, pad_csv, row_pred, bay_pred, rename_files


class TestIngestScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vineyard, cls.block, cls.date = "v", "b", "2020-01-01"
        cls.rows, cls.bays, cls.num_images = 21, 21, 4
        cls.f_org = f.file_org(
            cls.vineyard,
            cls.block,
            cls.date,
            rows=cls.rows,
            bays=cls.bays,
            images_per_bay=cls.num_images,
        )

        cls.f_org.gen_images()

    def testGenCSV(self):
        gen_csv.main(self.f_org, self)
        pad_csv.main(self.f_org, self)
        row_pred.main(self.f_org, self)
        bay_pred.main(self.f_org, self)
        rename_files.main(self.f_org, self)
