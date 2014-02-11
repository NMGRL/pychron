import string
import unittest

from blanks import BlankTest
from pychron.processing.dataset.tests.baselines import BaselineCorrectedTest
from pychron.processing.dataset.tests.isochron import IsochronTest
from pychron.processing.dataset.tests.signal import SignalsTest


class PlaceHolderTestCase(unittest.TestCase):
    pass


def tgen(tag, klass, i):
    t=string.ascii_uppercase[i]
    name=tag.format(t)
    bt=type(name,(klass, unittest.TestCase),
        {'analysis_id':i})
    globals()[name] = bt

for i in range(10):
    if i==8:
        #skip I
        continue
    tgen('BlanksTest{}',BlankTest, i)
    tgen('BaselinesTest{}',BaselineCorrectedTest, i)
    tgen('SignalsTest_{}',SignalsTest, i)
    tgen('IsochronTest_{}',IsochronTest, i)




if __name__=='__main__':
    unittest.main()