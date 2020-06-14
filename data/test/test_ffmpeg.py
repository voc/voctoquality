import unittest
import shutil
from os import path, makedirs
import libquality.ffmpeg as ffmpeg

basedir = path.dirname(path.realpath(__file__))


class TestFFmpeg(unittest.TestCase):
    tmpdir = path.join(basedir, "tmp/ffmpeg")

    def test_probeRate(self):
        reference = path.join(basedir, "fixtures/reference.nut")
        rate = ffmpeg.probe_rate(reference)
        self.assertAlmostEqual(rate, 190.137, places=3)

    def test_probeFail(self):
        reference = path.join(basedir, "fixtures/nonexistant___________.nut")
        rate = ffmpeg.probe_rate(reference)
        self.assertIsNone(rate)

    def test_decode(self):
        reference = path.join(basedir, "fixtures/reference.nut")
        dst = path.join(self.tmpdir, "decoded.nut")
        ffmpeg.decode(reference, dst)

    def test_decodeFail(self):
        reference = path.join(basedir, "fixtures/nonexistant___________.nut")
        dst = path.join(self.tmpdir, "notdecoded.nut")
        with self.assertRaises(ffmpeg.DecodeFailed):
            ffmpeg.decode(reference, dst)

    def setUp(self):
        makedirs(self.tmpdir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
