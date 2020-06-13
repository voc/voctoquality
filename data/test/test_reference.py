import unittest
import libquality.reference as reference
import shutil
import time
from os import path, stat

basedir = path.dirname(path.realpath(__file__))

class TestEnsure(unittest.TestCase):
    refdir = path.join(basedir, "tmp/references")

    def test_failedPrepare(self):
        sourcefile = path.join(basedir, "fixtures/invalid_url.json")
        with self.assertRaises(reference.ReferencePrepareFailed):
            references = reference.ensure_references(sourcefile, {"refdir": self.refdir})

    def test_failedHash(self):
        sourcefile = path.join(basedir, "fixtures/invalid_hash.json")
        with self.assertRaises(reference.InvalidSourceHash):
            references = reference.ensure_references(sourcefile, {"refdir": self.refdir})

    def test_downloadsSources(self):
        now = time.time()
        sourcefile = path.join(basedir, "fixtures/valid_sources.json")
        references = reference.ensure_references(sourcefile, {"refdir": self.refdir})
        self.assertEqual(references, [path.join(self.refdir, "fnord.nut"), path.join(self.refdir, "bahnmining.nut")])

        for ref in references:
            # files should be under refdir
            self.assertEqual(path.dirname(ref), self.refdir)

            # files should be present
            st = stat(ref)

            # files should be new
            self.assertTrue(st.st_ctime > now)

    def tearDown(self):
        shutil.rmtree(self.refdir, ignore_errors=True)
