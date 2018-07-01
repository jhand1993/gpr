import master
import pathlib as pl
import os


class TestPrimer(master.MasterGrabber):
    def __init__(
        self, testdir
    ):
        super().__init__()
        self.testdir = self.fdir / testdir
        self.testdir.mkdir(exist_ok=True)


test = TestPrimer('testdir')
print(test.fdir)
print(os.getcwd())
os.chdir(test.testdir)
print(os.getcwd())