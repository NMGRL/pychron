# ===============================================================================
# Copyright 2014 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import Property, cached_property, Button, HasTraits
from traitsui.api import View
# ============= standard library imports ========================
import itertools
from uncertainties import nominal_value, std_dev
import yaml
from scipy.stats import norm
# ============= local library imports  ==========================
from pychron.core.helpers.formatting import floatfmt
from pychron.core.helpers.logger_setup import logging_setup
from pychron.core.progress import progress_loader
from pychron.loggable import Loggable
from pychron.processing.analyses.file_analysis import FileAnalysis
from pychron.processing.permutator.view import PermutatorResultsView
from pychron.pipeline.plot.editors.ideogram_editor import IdeogramEditor
from pychron.pychron_constants import ARGON_KEYS


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


class PermutationRecord(object):
    __slots__ = ('age', 'info_str', 'identifier')


class FitPermutator(Loggable):
    def permutate(self, ai):
        func = lambda x, prog, i, n: self._permutate(ai, x, prog, i, n)

        perms = self._gen_unique_permutations(ai.isotopes)
        records = progress_loader(perms, func)

        # xs, es = zip(*((nominal_value(r.age), std_dev(r.age)) for r in records))
        # wm, we = calculate_weighted_mean(xs, es)
        return records

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
        identifier = ai.identifier

        self.debug('{} age: {:<20s} permutation: {}'.format(record_id, agestr, permstr))
        if prog:
            prog.change_message('Permutated {}: age: {}, perm:{}'.format(record_id,
                                                                         agestr, permstr))
        r = PermutationRecord()
        r.age = ai.uage
        r.info_str = '{} ({})'.format(record_id, permstr)
        r.identifier = identifier
        return r


class ICPermutator(Loggable):
    """
        do a monte carlo simulation on the CDD ICFactor
    """

    def permutate(self, ai):
        icf = ai.get_ic_factor('CDD')
        e = std_dev(icf)
        record_id = ai.record_id
        icf = 1.001
        e = 0.1
        perms = norm.rvs(loc=nominal_value(icf), scale=e, size=20)
        iso36 = ai.isotopes['Ar36']
        iso36.detector = 'CDD'

        func = lambda x, prog, i, n: self._permutate(ai, record_id, e, x, prog, i, n)
        records = progress_loader(perms, func)
        return records

    def _permutate(self, ai, record_id, e, ici, prog, i, n):
        if prog:
            prog.change_message('Setting ic_factor to {}, {}'.format(ici, e))

        ai.set_ic_factor('CDD', ici, e)

        ai.calculate_age(force=True)
        r = PermutationRecord()
        r.age = ai.uage
        r.info_str = '{} (ic={},{})'.format(record_id, floatfmt(ici), floatfmt(e))
        r.identifier = ai.identifier
        return r


class Permutator(Loggable):
    configuration_dict = Property

    @cached_property
    def _get_configuration_dict(self):
        try:
            with open(self.path, 'r') as rfile:
                return yaml.load(rfile)
        except yaml.YAMLError, e:
            self.warning('Invalid configuration file {}. error: {}'.format(self.path, e))

    def get_fits(self):
        return self.configuration_dict.get('permutations').get('fit')

    def _do_permutation(self, permutator):
        editor = self._setup_ideo_editor()

        ans = []
        gid, ggid = 0, 0
        group = True
        graph = False

        v = PermutatorResultsView()
        for i, ai in enumerate(self.oanalyses):
            records = permutator.permutate(ai)
            if group:
                gid = i
            elif graph:
                ggid = i

            v.append_results(records)
            ans.extend(self._make_analyses(records, gid, ggid))

        editor.analyses = ans
        editor.rebuild()
        v.editor = editor
        v.edit_traits()

    def ic_permutation(self):
        ic = ICPermutator()
        self._do_permutation(ic)

    def fits_permutation(self):
        fp = FitPermutator()
        fp.fits = self.get_fits()
        self._do_permutation(fp)

    def _setup_ideo_editor(self):
        editor = IdeogramEditor()
        po = editor.plotter_options_manager.plotter_options
        po.set_aux_plot_height('Analysis Number Nonsorted', 300)
        editor.disable_aux_plots()
        return editor

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
            # self.permutator.fits_permutation()
            self.permutator.ic_permutation()

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
                             # Record('39b6e623-e178-4dc4-bf5c-14c81485bd54')
                             ],
                            use_cache=False, unpack=True)
    # a.j = ufloat(1e-4, 1e-7)

    p.oanalyses = ans

    # p.fits_permutation()
    v = PermutatorView(permutator=p)
    v.configure_traits()
# ============= EOF =============================================
