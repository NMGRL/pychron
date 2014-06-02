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
from traits.api import Int, on_trait_change, Str, Property, cached_property, Float, Bool, HasTraits, Instance
from traitsui.api import View, Item, EnumEditor, VGroup, HGroup
# ============= standard library imports ========================
import ast
import yaml
# ============= local library imports  ==========================
from pychron.core.helpers.ctx_managers import no_update
from pychron.core.helpers.filetools import list_directory2
from pychron.paths import paths
from pychron.pyscripts.context_editors.context_editor import ContextEditor


class YamlObject(HasTraits):
    name = ''

    def load(self, ctx):
        try:
            for k, v in ctx[self.name].items():
                setattr(self, k, v)
        except KeyError:
            pass

    def dump(self):
        def get(k):
            v = getattr(self, k)
            if isinstance(v, unicode):
                v = str(v)
            return v

        return {k: get(k)
                for k in self.trait_names() if not k in ('trait_added', 'trait_modified', 'name')}


class Multicollect(YamlObject):
    name = 'multicollect'
    counts = Int(enter_set=True, auto_set=False)
    isotope = Str(enter_set=True, auto_set=False)
    detector = Str(enter_set=True, auto_set=False)


class Baseline(YamlObject):
    name = 'baseline'
    detector = Str(enter_set=True, auto_set=False)
    mass = Float(enter_set=True, auto_set=False)
    counts = Int(enter_set=True, auto_set=False)
    before = Bool
    after = Bool


class PeakCenter(YamlObject):
    name = 'peakcenter'
    before = Bool
    after = Bool
    isotope = Str(enter_set=True, auto_set=False)
    detector = Str(enter_set=True, auto_set=False)


class Equilibration(YamlObject):
    name = 'equilibration'
    inlet = Str(enter_set=True, auto_set=False)
    outlet = Str(enter_set=True, auto_set=False)
    inlet_delay = Int(enter_set=True, auto_set=False)


class MeasurementContextEditor(ContextEditor):
    # context values
    multicollect = Instance(Multicollect, ())
    baseline = Instance(Baseline, ())
    peakcenter = Instance(PeakCenter, ())
    equilibration = Instance(Equilibration, ())

    # general
    default_fits = Str(enter_set=True, auto_set=False)
    available_default_fits = Property

    #persistence
    def load(self, s):
        with no_update(self):

            try:
                s = self._extract_docstring(s)
            except SyntaxError:
                return

            if s:
                ctx = yaml.load(s)
                self.multicollect.load(ctx)
                self.baseline.load(ctx)
                self.peakcenter.load(ctx)
                self.equilibration.load(ctx)

                self.default_fits = ctx.get('default_fits', '')

    def dump(self):
        ctx = dict(default_fits=self.default_fits,
                   multicollect=self.multicollect.dump(),
                   baseline=self.baseline.dump(),
                   peakcenter=self.peakcenter.dump(),
                   equilibration=self.equilibration.dump())

        return yaml.dump(ctx, default_flow_style=False)

    def generate_docstr(self):
        def gen():
            yield "'''"
            for di in reversed(self.dump().split('\n')):
                if di.strip():
                    yield di
            yield "'''"

        return list(gen())

    def _extract_docstring(self, s):
        m = ast.parse(s)
        return ast.get_docstring(m)

    @on_trait_change('multicollect:+, baseline:+, peakcenter:+, equilibration:+, default_fits')
    def request_update(self):
        if self._no_update:
            return

        self.update_event = True

    @cached_property
    def _get_available_default_fits(self):
        return list_directory2(paths.fits_dir, extension='.yaml', remove_extension=True)

    def traits_view(self):
        mc_grp = VGroup(
            Item('object.multicollect.counts'),
            Item('object.multicollect.isotope'),
            Item('object.multicollect.detector'),
            show_border=True,
            label='Multicollect')

        bs_grp = VGroup(Item('object.baseline.counts'),
                        Item('object.baseline.mass'),
                        HGroup(Item('object.baseline.before'),
                               Item('object.baseline.after')),
                        show_border=True, label='Baseline')

        pc_grp = VGroup(
            Item('object.peakcenter.isotope'),
            Item('object.peakcenter.detector'),
            HGroup(Item('object.peakcenter.before'),
                   Item('object.peakcenter.after')),
            show_border=True, label='PeakCenter')

        eq_grp = VGroup(Item('object.equilibration.inlet'),
                        Item('object.equilibration.outlet'),
                        Item('object.equilibration.inlet_delay'))
        gen_grp = VGroup(Item('default_fits',
                              editor=EnumEditor(name='available_default_fits')),
                         show_border=True,
                         label='General')

        v = View(VGroup(gen_grp, mc_grp, bs_grp, pc_grp, eq_grp))
        return v

# ============= EOF =============================================
