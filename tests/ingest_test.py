import unittest


import __init__
from tests.mocks import file_org as f
import os

from ingest.internal import gen_csv, pad_csv, row_pred, bay_pred, rename_files


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

        cls.raw_dir = cls.f_org.get_image_path(
            cls.vineyard, cls.block, cls.date)
        cls.f_org.gen_images()

    def testGenCSV_BySteps(self):
        gen_csv.main(self.f_org, self)
        pad_csv.main(self.f_org, self)
        row_pred.main(self.f_org, self)
        bay_pred.main(self.f_org, self)
        rename_files.main(self.f_org, self)

    def testGenCSV_Sequentially(self):
        steps = [
            gen_csv.main,
            pad_csv.main,
            row_pred.main,
            bay_pred.main,
            rename_files.main,
        ]

        df = None
        for s in steps:
            df = s(self.f_org, self, df=df)
