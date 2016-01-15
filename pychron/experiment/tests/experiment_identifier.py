from pychron.experiment.automated_run.spec import AutomatedRunSpec
from pychron.experiment.utilities.identifier import is_special
from pychron.experiment.utilities.repository_identifier import retroactive_experiment_identifiers

__author__ = 'ross'

import unittest


class DummyExecutor(object):
    def __init__(self):
        self.cruns = []
        self.expid = None
        self.associations = []

    def retroactive_experiment_identifiers(self, spec):
        # print '{} added to {}'.format(spec.experiment_id, spec.runid)
        self.cruns, self.expid = retroactive_experiment_identifiers(spec, self.cruns, self.expid)

        self.associate(spec.repository_identifier, spec.runid)
        if not is_special(spec.identifier) and self.cruns:
            for c in self.cruns:
                # print 'add {} {} {}'.format(self.expid, c.experiment_id, c.runid)
                self.associate(self.expid, c.runid)
            self.cruns = []

    def associate(self, e, r):
        if e:
            args = (e, r)
            if args not in self.associations:
                self.associations.append(args)


class ExperimentIdentifierTestCase(unittest.TestCase):
    # def test_single_blank(self):
    #     d = DummyExecutor()
    #     aspec = AutomatedRunSpec(identifer='bu-FD-j', experiment_id='foo')
    #     bspec = AutomatedRunSpec(identifer='10000', experiment_id='foo')
    #     retroactive_experiment_identifiers(aspec, d.cruns, d.expid)
    #     retroactive_experiment_identifiers(bspec, d.cruns, d.expid)
    #
    #     self.assertEqual(aspec.experiment_id, 'foo')
    #     self.assertEqual(bspec.experiment_id, 'foo')
    #
    # def test2(self):
    #     d = DummyExecutor()
    #     spec = AutomatedRunSpec(identifier='bu-FD-j', aliquot=1, experiment_id='foo')
    #     d.retroactive_experiment_identifiers(spec)
    #
    #     spec = AutomatedRunSpec(identifier='10000', experiment_id='foo')
    #     d.retroactive_experiment_identifiers(spec)
    #
    #     spec = AutomatedRunSpec(identifier='bu-FD-j', aliquot=2, experiment_id='foo')
    #     d.retroactive_experiment_identifiers(spec)
    #
    #     spec = AutomatedRunSpec(identifier='20000', experiment_id='bar')
    #     d.retroactive_experiment_identifiers(spec)
    #
    #     spec = AutomatedRunSpec(identifier='20000', aliquot=1, experiment_id='bar')
    #     d.retroactive_experiment_identifiers(spec)
    #
    #     self.assertListEqual(d.associations, [('foo', 'bu-FD-j-01'),
    #                                           ('foo','10000-00'),
    #                                           ('foo','bu-FD-j-02'),
    #                                           ('bar', '20000-00'),
    #                                           ('bar','bu-FD-j-02'),
    #                                           ('bar','20000-01')])

    def test3(self):
        d = DummyExecutor()
        spec = AutomatedRunSpec(identifier='bu-FD-j', aliquot=1)
        d.retroactive_experiment_identifiers(spec)

        spec = AutomatedRunSpec(identifier='bu-FD-j', aliquot=2)
        d.retroactive_experiment_identifiers(spec)

        spec = AutomatedRunSpec(identifier='10000', repository_identifier='foo')
        d.retroactive_experiment_identifiers(spec)

        spec = AutomatedRunSpec(identifier='20000', repository_identifier='bar')
        d.retroactive_experiment_identifiers(spec)

        spec = AutomatedRunSpec(identifier='20000', aliquot=1, repository_identifier='bar')
        d.retroactive_experiment_identifiers(spec)

        spec = AutomatedRunSpec(identifier='bu-FD-j', aliquot=3)
        d.retroactive_experiment_identifiers(spec)

        self.assertListEqual(d.associations, [
                                              ('foo','10000-00'),
                                              ('foo', 'bu-FD-j-01'),
                                              ('foo','bu-FD-j-02'),
                                              ('bar', '20000-00'),
                                              ('bar','20000-01'),
                                              ('bar','bu-FD-j-03'),
                                              ])
if __name__ == '__main__':
    unittest.main()
