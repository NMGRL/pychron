import math
import os

from pychron.core.ui import set_toolkit

set_toolkit('qt4')

from pychron.processing.autoupdate_parser import AutoupdateParser
from test.database import isotope_manager_factory

isotope_man=isotope_manager_factory(name='pychron_dataset')
isotope_man.db.connect(test=True)

pp = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'massspec_dataset_nofilter')
# pp = '../data/massspec_dataset_nofilter'
parser = AutoupdateParser()
parser.parse(pp)

msid='Unknown'
sid='MB06-507'
pid='Minna Bluff'

class IntensityMixin(object):
    @classmethod
    def setUpClass(cls):
        aid=cls.analysis_id
        cls.sample_id = msid
        cls.analysis_id = aid
        db=isotope_man.db
        with db.session_ctx():
            ans, tc = db.get_sample_analyses([sid, ], [pid])
            an = isotope_man.make_analysis(ans[aid])

            cls.analysis = an

        cls.parser=parser

    def setup(self):
        for k in ('Ar40','Ar39'):
            setattr(self, 'test_{}_blank'.format(k),
                    lambda: self._blank(k))
            setattr(self, 'test_{}_blank_err'.format(k),
                    lambda: self._blank_err(k))

    def _almost_equal(self, v, k):
        ev, cnt = self.get_expected_value(k)

        sv = str(v)
        acnt = 10000
        if 'e' in sv:
            acnt = int(round(abs(math.log10(v))))
        elif '.' in sv:
            a = sv.split('.')[-1]
            acnt = len(a)

        cnt = min(acnt, cnt)
        self.assertAlmostEqual(v, ev, cnt)

    #util
    def get_expected_value(self, k):
        p = self.parser
        p.parse(pp)
        s = p.samples[self.sample_id]
        an = s.analyses[self.analysis_id]
        ev = getattr(an, k)
        try:
            sev = str(ev)
            if '.' in sev:
                cnt = len(str(ev).split('.')[1])
            else:
                cnt = int(abs(math.log(ev, 10)))
        except ValueError:
            ev,cnt=0,1

        return ev,cnt

    def _almost_equal(self, v, k):
        ev, cnt = self.get_expected_value(k)

        sv = str(v)
        acnt = 10000
        if 'e' in sv:
            acnt = int(round(abs(math.log10(v))))
        elif '.' in sv:
            a = sv.split('.')[-1]
            acnt = len(a)

        cnt = min(acnt, cnt)

        # dev=abs(v-ev)/v*1000
        # self.assertLess(dev, 1)
        self.assertAlmostEqual(v, ev, cnt-1)

