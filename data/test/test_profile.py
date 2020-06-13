import unittest
from libquality.profiles.simple import SimpleProfile
import shutil
import time
from os import path, stat

basedir = path.dirname(path.realpath(__file__))

class TestSimpleProfile(unittest.TestCase):
    tmpdir = path.join(basedir, "tmp/profile")

    def setUp(self):
        self.profile = SimpleProfile()

    def test_process(self):
        reference = path.join(basedir, "fixtures/reference.nut")
        results = [{'reference': 'reference', 'profile': 'simple', 'tag': 'testing', 'codec': 'copy', 'opts': '-i $ref -c:v copy', 'speed': 89.6, 'rate': 116135.56, 'score_mean': 99.26749500000001, 'score_harm_mean': 99.254729088278, 'score_10th_pct': 98.49073, 'score_min': 98.42804}, {'reference': 'reference', 'profile': 'simple', 'tag': 'testing', 'codec': 'libvpx-vp9', 'opts': '-i $ref -c:v libvpx-vp9', 'speed': 1.04, 'rate': 81.973, 'score_mean': 85.56661600000001, 'score_harm_mean': 82.5296607669634, 'score_10th_pct': 73.33489, 'score_min': 51.29036}, {'reference': 'reference', 'profile': 'simple', 'tag': 'testing', 'codec': 'libx264', 'opts': '-i $ref -c:v libx264', 'speed': 4.06, 'rate': 224.868, 'score_mean': 98.03638800000002, 'score_harm_mean': 97.99567274453702, 'score_10th_pct': 96.49025, 'score_min': 96.38498}, {'reference': 'reference', 'profile': 'simple', 'tag': 'testing', 'codec': 'libx265', 'opts': '-i $ref -c:v libx265', 'speed': 2.02, 'rate': 78.706, 'score_mean': 96.59885399999999, 'score_harm_mean': 96.53314263881514, 'score_10th_pct': 94.4406, 'score_min': 94.04528}]

        for got, expected in zip(self.profile.process(reference, "testing", self.tmpdir), results):
            # sometimes we do not get a speed?
            if "speed" in got:
                del got["speed"]

            del expected["speed"]
            self.assertEqual(got, expected, msg=f"result for {expected['codec']} changed")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
