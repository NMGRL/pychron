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
from traits.api import Int, on_trait_change, Str, Property, cached_property, \
    Float, Bool, HasTraits, Instance, TraitError, Button
from traitsui.api import View, Item, EnumEditor, VGroup, HGroup
# ============= standard library imports ========================
import os
import ast
import yaml
# ============= local library imports  ==========================
from pychron.core.helpers.ctx_managers import no_update
from pychron.core.helpers.filetools import list_directory2
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.paths import paths
from pychron.pyscripts.context_editors.context_editor import ContextEditor
from pychron.pyscripts.hops_editor import HopEditorModel, HopEditorView


class YamlObject(HasTraits):
    name = ''

    def load(self, ctx):
        try:
            for k, v in ctx[self.name].items():
                setattr(self, k, v)
        except (KeyError, TraitError):
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
    use_extraction_eqtime = Bool
    eqtime = Float(enter_set=True, auto_set=False)


class PeakHop(YamlObject):
    name = 'peakhop'
    use_peak_hop = Bool
    hops_name = Str


class MeasurementContextEditor(ContextEditor):
    # context values
    multicollect = Instance(Multicollect, ())
    baseline = Instance(Baseline, ())
    peakcenter = Instance(PeakCenter, ())
    equilibration = Instance(Equilibration, ())
    peakhop = Instance(PeakHop, ())

    # general
    default_fits = Str(enter_set=True, auto_set=False)
    available_default_fits = Property

    available_hops = Property

    edit_peakhop_button = Button

    # persistence
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
                self.peakhop.load(ctx)

                self.default_fits = ctx.get('default_fits', '')

    def dump(self):
        ctx = dict(default_fits=self.default_fits,
                   multicollect=self.multicollect.dump(),
                   baseline=self.baseline.dump(),
                   peakcenter=self.peakcenter.dump(),
                   equilibration=self.equilibration.dump(),
                   peakhop=self.peakhop.dump())

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

    def _edit_peakhop_button_fired(self):
        name = self.peakhop.hops_name
        if name:
            p = os.path.join(paths.measurement_dir, 'hops', '{}.txt'.format(name))

            pem = HopEditorModel()
            pem.open(p)
            pev = HopEditorView(model=pem)
            pev.edit_traits(kind='livemodal')

    def _use_extraction_eqtime_changed(self, new):
        if new:
            self.equilibration.eqtime = 'eqtime'
        else:
            self.equilibration.eqtime = 15

    @on_trait_change('peakhop:+, multicollect:+, baseline:+, peakcenter:+, equilibration:+, default_fits')
    def request_update(self):
        if self._no_update:
            return

        self.update_event = True

    @cached_property
    def _get_available_default_fits(self):
        return list_directory2(paths.fits_dir, extension='.yaml', remove_extension=True)

    @cached_property
    def _get_available_hops(self):
        return list_directory2(os.path.join(paths.measurement_dir, 'hops'),
                               extension='.txt', remove_extension=True)

    def traits_view(self):
        mc_grp = VGroup(
            Item('object.multicollect.counts'),
            Item('object.multicollect.isotope'),
            Item('object.multicollect.detector'),
            show_border=True, label='Multicollect')

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
                        Item('object.equilibration.inlet_delay'),
                        Item('object.equilibration.use_extraction_eqtime'),
                        Item('object.equilibration.eqtime',
                             enabled_when='not object.equilibration.use_extraction_eqtime',
                             label='Duration'),
                        show_border=True, label='Equilibration')
        ph_grp = VGroup(Item('object.peakhop.use_peak_hop'),
                        HGroup(Item('object.peakhop.hops_name',
                                    label='Hops',
                                    editor=EnumEditor(name='available_hops')),
                               icon_button_editor('edit_peakhop_button', 'cog',
                                                  enabled_when='object.peakhop.hops_name',
                                                  tooltip='Edit selected "Hops" file')),
                        show_border=True, label='Peak Hop')

        gen_grp = VGroup(Item('default_fits',
                              editor=EnumEditor(name='available_default_fits')),
                         show_border=True, label='General')

        #using VFold causing crash. just use VGroup for now
        # v = View(VFold(gen_grp, mc_grp, bs_grp, pc_grp, eq_grp, ph_grp))
        v = View(VGroup(gen_grp, mc_grp, bs_grp, pc_grp, eq_grp, ph_grp))
        return v

# ============= EOF =============================================
