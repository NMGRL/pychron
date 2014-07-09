import os
import itertools

from traits.api import Property, cached_property
from uncertainties import ufloat, nominal_value, std_dev
import yaml
from numpy import array
from pychron.core.helpers.logger_setup import logging_setup
from pychron.core.stats.core import calculate_weighted_mean
from pychron.loggable import Loggable
from pychron.processing.arar_age import ArArAge


# class PermutationResults(object):
# def __init__(self):
#         self.permutations = []
#
#     def add(self, r):
#         self.permutations.append(r)
#
# class PermutatedAnalysis(ArArAge):
#     pass
#     # def __init__(self, a, *args, **kw):
#     #     super(PermutatedAnalysis, self).__init__(*args, **kw)
#     #     self.isotopes =


class FitPermutator(Loggable):
    permutations = Property

    def gen_permutations(self):
        n = 5
        ifits = [self.fits for i in range(n)]
        return itertools.product(*ifits)

    def permutate(self, ai):
        f = self._permutate
        ages = [f(ai, perm) for perm in self.gen_permutations()]
        xs, es = zip(*((nominal_value(x), std_dev(x)) for x in ages))
        wm, we = calculate_weighted_mean(xs, es)
        return wm, ages

    def _permutate(self, ai, perm):
        for iso, p in zip(ai.isotopes.itervalues(), perm):
            iso.set_fit(p)
            iso.dirty = True
        ai.calculate_age(force=True)
        self.debug('age: {:<20s} permutation: {}'.format(str(ai.uage), ','.join(perm)))
        return ai.uage


class Permutator(Loggable):
    configuration_dict = Property

    @cached_property
    def _get_configuration_dict(self):
        try:
            with open(self.path, 'r') as fp:
                return yaml.load(fp)
        except yaml.YAMLError, e:
            self.warning('Invalid configuration file {}. error: {}'.format(self.path, e))

    def get_fits(self):
        return self.configuration_dict.get('permutations').get('fits')

    def fits_permutation(self):
        fp = FitPermutator()
        fp.fits = self.get_fits()
        for ai in self.oanalyses:
            wm, ages = fp.permutate(ai)
            print wm

if __name__ == '__main__':
    p = Permutator()
    p.path = './tests/data/config.yaml'
    logging_setup('perm')

    from pychron.database.isotope_database_manager import IsotopeDatabaseManager

    class Record(object):
        uuid = 'd48e3d9f-4d46-4af6-8815-4820a8e62a1b'
        analysis_type = 'unknown'

    man = IsotopeDatabaseManager(bind=False, connect=False)
    db = man.db
    db.trait_set(kind='mysql',
                 host='129.138.12.160',
                 name='pychrondata',
                 user='root', password='DBArgon')
    db.connect()

    a = man.make_analysis(Record(), use_cache=False, unpack=True)
    a.j = ufloat(1e-4, 1e-7)
    p.oanalyses = [a]

    p.fits_permutation()

