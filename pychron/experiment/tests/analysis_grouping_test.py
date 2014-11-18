from pychron.experiment.automated_run.persistence import AutomatedRunPersister
from pychron.experiment.automated_run.spec import AutomatedRunSpec

__author__ = 'ross'

import unittest

runs = [('references', 'bu-j-1', 'b1'), ('A', '11111', 'u1'),
        ('references', 'bu-j-2', 'b2'), ('B','22222','u2'), ('B','33333','u3')]

class MockDB(object):
    def __init__(self):
        self.groups = {}
        self._cnt = 0

    def get_analysis_group(self, prj, **kw):
        if not prj in self.groups:
            self.groups[prj] = MockAnalysisGroup()

        return self.groups[prj]

    def add_analysis_group_set(self, ag, analysis):
        ag.analyses.append(analysis)
        print 'adding {}, {}'.format(analysis.uuid, len(ag.analyses))

    def get_last_analysis(self, **kw):
        if self._cnt==0:
            pass
        else:
            m = MockAnalysis()
            m.uuid='12345'
            m.project='A'
            return m
        self._cnt+=1

    def get_analysis_uuid(self, u):
        t = next((r for r in runs if r[2]==u), None)
        if t:
            m=MockAnalysis()
            m.uuid=u
            m.rid = t[1]
            return m


class MockAnalysisGroup(object):
    def __init__(self):
        self.analyses = []


class MockAnalysis(object):
    project = ''
    @property
    def project_name(self):
        return self.project


class MockRunSpec(object):
    project = ''


def gen_mock_analysis():
    for _, _, u in runs:
        m = MockAnalysis()
        m.uuid = u
        yield m


def gen_mock_runspec():
    for p, l, _ in runs:
        rs = AutomatedRunSpec()
        rs.project = p
        rs.labnumber = l
        yield rs





class MyTestCase(unittest.TestCase):
    # @classmethod
    # def setUpClass(cls):
    #     cls.persister =

    def setUp(self):
        self.mock_analyses = gen_mock_analysis()
        self.runspecs = gen_mock_runspec()
        self.persister =AutomatedRunPersister()
        self.db = MockDB()

    def test_save_group(self):
        per = self.persister
        db = self.db
        per.run_spec = self.runspecs.next()

        analysis = self.mock_analyses.next()
        per._save_analysis_group(db, analysis)
        self.assertEqual(True, True)

    def test_save_group_sequence1(self):
        per = self.persister
        db = self.db
        for i in range(3):
            per.run_spec = self.runspecs.next()

            analysis = self.mock_analyses.next()
            per._save_analysis_group(db, analysis)

        for a in db.groups['A-autogen'].analyses:
            print a.uuid

        uuids = [a.uuid for a in db.groups['A-autogen'].analyses]
        self.assertEqual(uuids, ['u1','b1','b2'])

    def test_save_group_sequence2(self):
        per = self.persister
        db = self.db
        for i in range(5):
            per.run_spec = self.runspecs.next()

            analysis = self.mock_analyses.next()
            per._save_analysis_group(db, analysis)

        # for a in db.groups['B-autogen'].analyses:
        #     print a.uuid

        uuids = [a.uuid for a in db.groups['B-autogen'].analyses]
        self.assertEqual(uuids, ['u2','b2','u3'])

if __name__ == '__main__':
    unittest.main()
