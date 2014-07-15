import itertools

from traits.api import Property, cached_property, Button, HasTraits
from traitsui.api import View

from uncertainties import nominal_value, std_dev
import yaml

from pychron.core.helpers.logger_setup import logging_setup
from pychron.core.progress import progress_loader
from pychron.core.stats.core import calculate_weighted_mean
from pychron.loggable import Loggable
from pychron.processing.analyses.file_analysis import FileAnalysis


# class PermutationResults(object):
# def __init__(self):
# self.permutations = []
#
#     def add(self, r):
#         self.permutations.append(r)
#
# class PermutatedAnalysis(ArArAge):
#     pass
#     # def __init__(self, a, *args, **kw):
#     #     super(PermutatedAnalysis, self).__init__(*args, **kw)
#     #     self.isotopes =
from pychron.processing.tasks.figures.editors.ideogram_editor import IdeogramEditor
from pychron.pychron_constants import ARGON_KEYS


class PermutationRecord(object):
    __slots__ = ('age', 'info_str')


class FitPermutator(Loggable):
    def permutate(self, ai):
        func = lambda x, prog, i, n: self._permutate(ai, x, prog, i, n)

        perms = self._gen_unique_permutations(ai.isotopes)
        records = progress_loader(perms, func)

        xs, es = zip(*((nominal_value(r.age), std_dev(r.age)) for r in records))
        wm, we = calculate_weighted_mean(xs, es)
        return wm, records

    def _gen_unique_permutations(self, isos):
        n = 5

        skips = self.fits['skips']
        ifits = (self.fits['fits'] for _ in range(n))

        rs = []
        for perm in itertools.product(*ifits):
            nperm = []
            for k, p in zip(ARGON_KEYS, perm):
                iso = isos[k]
                if k in skips:
                    p = iso.fit
                nperm.append((k, p))
            if nperm not in rs:
                rs.append(nperm)

        return rs

    def _permutate(self, ai, perm, prog, i, n):
        isos = ai.isotopes
        ps = []
        for k, p in perm:
            iso = isos[k]
            iso.set_fit(p)
            iso.dirty = True
            ps.append(p[0])

        ai.calculate_age(force=True)

        permstr = ','.join(ps)
        agestr = str(ai.uage)
        record_id = ai.record_id
        self.debug('{} age: {:<20s} permutation: {}'.format(record_id, agestr, permstr))
        if prog:
            prog.change_message('Permutated {}: age: {}, perm:{}'.format(record_id,
                                                                         agestr, permstr))
        r = PermutationRecord()
        r.age = ai.uage
        r.info_str = '{} ({})'.format(record_id, permstr)
        return r


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
        return self.configuration_dict.get('permutations').get('fit')

    def fits_permutation(self):
        fp = FitPermutator()
        fp.fits = self.get_fits()

        editor = IdeogramEditor()
        po = editor.plotter_options_manager.plotter_options
        po.set_aux_plot_height('Analysis Number Stacked', 300)
        editor.disable_aux_plots()

        ans = []
        gid, ggid = 0, 0
        group = True
        graph = False
        for i, ai in enumerate(self.oanalyses):
            wm, records = fp.permutate(ai)
            if group:
                gid = i
            elif graph:
                ggid = i

            ans.extend(self._make_analyses(records, gid, ggid))

        editor.analyses = ans
        editor.rebuild()
        editor.edit_traits()

    def _make_analyses(self, records, gid, ggid):

        return [FileAnalysis(age=nominal_value(ai.age),
                             age_err=std_dev(ai.age),
                             record_id=ai.info_str,
                             group_id=gid,
                             graph_id=ggid)
                for ai in records]


if __name__ == '__main__':
    class PermutatorView(HasTraits):
        test = Button

        def _test_fired(self):
            self.permutator.fits_permutation()

        def traits_view(self):
            v = View('test')
            return v

    p = Permutator()
    p.path = './tests/data/config.yaml'
    logging_setup('perm')

    from pychron.database.isotope_database_manager import IsotopeDatabaseManager

    class Record(object):
        analysis_type = 'unknown'

        def __init__(self, u):
            self.uuid = u

    man = IsotopeDatabaseManager(bind=False, connect=False)
    db = man.db
    db.trait_set(kind='mysql',
                 host='localhost',
                 name='pychrondata_dev',
                 username='root', password='Argon')
    db.connect()

    ans = man.make_analyses([Record('65c1c4a9-e317-452b-9654-3f06efcbe664'),
                             Record('39b6e623-e178-4dc4-bf5c-14c81485bd54')],
                            use_cache=False, unpack=True)
    # a.j = ufloat(1e-4, 1e-7)

    p.oanalyses = ans

    # p.fits_permutation()
    v = PermutatorView(permutator=p)
    v.configure_traits()
