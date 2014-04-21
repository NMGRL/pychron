#===============================================================================
# Copyright 2014 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits, List, on_trait_change, Bool, Event
from traitsui.api import View, UItem, TableEditor, HGroup, spring, Handler, VGroup, Group

#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.table_column import ObjectColumn
from pychron.envisage.tasks.pane_helpers import icon_button_editor


class AnalysisEditViewHandler(Handler):
    def closed(self, info, isok):
        if not isok:
            info.object.revert()
        info.object.clear()


class AnalysisEditView(HasTraits):
    isotopes = List
    baselines = List
    blanks = List
    revert_button = Event
    dirty = Bool

    control = None
    editor = None

    def __init__(self, editor, *args, **kw):
        super(AnalysisEditView, self).__init__(*args, **kw)
        self.editor = editor
        self.load()

    def load(self):
        m = self.editor.model
        self.title = 'Edit Data - {}'.format(m.record_id)
        self.load_isotopes()

    def load_isotopes(self):
        isos = self.editor.model.isotopes
        ns = []
        bks = []
        bs = []
        for k in self.editor.model.isotope_keys:
            iso = isos[k]
            iso.use_static = True
            ns.append(iso)
            bks.append(iso.blank)
            bs.append(iso.baseline)

        self.isotopes = ns
        self.blanks = bks
        self.baselines = bs

        # self.isotopes = [isos[k] for k in self.editor.model.isotope_keys]

    @on_trait_change('[isotopes,blanks,baselines]:[_value,_error]')
    def _handle_change(self, obj, name, old, new):
        self.dirty = True
        obj.dirty = True
        model = self.editor.model
        model.calculate_age(force=True)
        model.analysis_view.main_view.load(model, refresh=True)

    def _revert_button_fired(self):
        self.revert()

    def show(self):
        self.control.raise_()

    def clear(self):
        for iso in self.isotopes:
            iso.use_static = False

        self.editor.edit_view = None
        self.control = None

    def revert(self):
        for iso in self.isotopes:
            iso.revert_user_defined()
        self.dirty = False

    def traits_view(self):
        cols = [ObjectColumn(name='name', editable=False),
                ObjectColumn(name='value'),
                ObjectColumn(name='error')]

        iso_grp = VGroup(UItem('isotopes',
                               editor=TableEditor(columns=cols,
                                                  sortable=False)),
                         label='Intercepts', show_border=True)

        baseline_grp = VGroup(UItem('baselines',
                                    editor=TableEditor(sortable=False,
                                                       columns=cols)),
                              label='Baselines', show_border=True)

        blank_grp = VGroup(UItem('blanks',
                                 editor=TableEditor(
                                     sortable=False,
                                     columns=cols)),
                           label='Blanks', show_border=True)

        bgrp = HGroup(icon_button_editor('revert_button',
                                         'arrow_undo',
                                         tooltip='Undo changes',
                                         enabled_when='dirty'), spring)

        v = View(VGroup(Group(iso_grp, baseline_grp, layout='tabbed'),
                        blank_grp, bgrp),
                 buttons=['OK', 'Cancel'],
                 handler=AnalysisEditViewHandler(),
                 resizable=True,
                 title=self.title,
                 x=0.05,
                 y=0.05)

        return v


#============= EOF =============================================
