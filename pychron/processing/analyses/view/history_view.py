# ===============================================================================
# Copyright 2013 Jake Ross
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
from chaco.array_data_source import ArrayDataSource
from pyface.action.menu_manager import MenuManager
from traits.api import HasTraits, List, Int, Any, Str, Event, on_trait_change, Instance
from traitsui.api import View, UItem, TabularEditor, VSplit, \
    Handler, HGroup
from traitsui.menu import Action
from traitsui.tabular_adapter import TabularAdapter
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.isotope_utils import sort_isotopes
from pychron.graph.stacked_regression_graph import StackedRegressionGraph
from pychron.processing.analyses.changes import BlankChange


class ChangeAdapter(TabularAdapter):
    font = 'arial 10'
    create_date_width = Int(120)


class BlankHistoryAdapter(ChangeAdapter):
    columns = [('Date', 'create_date'), ('Summary', 'summary')]

    def get_bg_color(self, object, trait, row, column=0):
        color = 'white'
        if self.item.active:
            color = '#B0C4DE'
        return color

    def get_menu(self, obj, trait, row, column):
        enabled = True
        if self.item.selected:
            enabled = bool(self.item.selected.values)

        diffable=len(obj.blank_selected)==2

        return MenuManager(Action(name='Show Time Series',
                                  action='show_blank_time_series',
                                  enabled=enabled),
                           Action(name='Apply Change', action='apply_blank_change'),
                           Action(name='Apply Change to Session', action='apply_session_blank_change'),
                           Action(name='Diff Selected', action='diff_blank_histories',
                                  enabled=diffable))


class FitHistoryAdapter(ChangeAdapter):
    columns = [('Date', 'create_date'), ('Summary', 'summary')]


class FitAdapter(TabularAdapter):
    font = 'arial 10'
    columns = [('Isotope', 'isotope'), ('Fit', 'fit')]


class IsotopeBlankAdapter(TabularAdapter):
    font = 'arial 10'
    columns = [('Isotope', 'isotope'), ('Fit', 'fit')]


class AnalysesAdapter(TabularAdapter):
    font = 'arial 10'
    columns = [('Run ID', 'record_id')]


class HistoryHandler(Handler):
    def show_blank_time_series(self, info, obj):
        obj.show_blank_time_series()

    def apply_blank_change(self, info, obj):
        # obj.apply_blank_change()
        obj.apply_blank_change_needed = (False, obj.blank_selected)

    def apply_session_blank_change(self, info, obj):
        # obj.apply_session_blank_change()
        obj.apply_blank_change_needed = (True, obj.blank_selected)

    def diff_blank_histories(self, info, obj):
        obj.diff_blank_histories()


class HistoryView(HasTraits):
    name = 'History'

    blank_changes = List
    fit_changes = List

    blank_selected = List
    blank_right_clicked = Any
    fit_selected = Any

    analysis_uuid = Str
    apply_blank_change_needed = Event
    refresh_needed = Event
    update_blank_selected = Event
    blank_selected_=Instance(BlankChange)
    # blank_selected_ = Property(depends_on='update_blank_selected')

    @on_trait_change('blank_selected[]')
    def _handle_blank_selected(self):
        # print self.blank_selected
        self.blank_selected_=self.blank_selected[0]

    def __init__(self, an, *args, **kw):
        super(HistoryView, self).__init__(*args, **kw)
        self._load(an)

    def load(self, an):
        self._load(an)

    def diff_blank_histories(self):
        from pychron.processing.analyses.view.blank_diff_view import BlankDiffView

        c = BlankDiffView()
        left, right = self.blank_selected
        c.load(left, right)
        c.edit_traits()

    def show_blank_time_series(self):
        g = StackedRegressionGraph(window_height=0.75)
        isotopes = self.blank_selected.isotopes
        keys = sort_isotopes([iso.isotope for iso in isotopes], reverse=False)
        _mi, _ma = None, None

        for k in keys:
            iso = next((i for i in isotopes if i.isotope == k))
            # print iso.analyses
            g.new_plot(padding_right=10)
            g.set_time_xaxis()
            g.set_y_title(iso.isotope)

            g.new_series([self.timestamp], [iso.value],
                         marker_size=3,
                         fit=False,
                         type='scatter', marker_color='black')
            vs = iso.values
            if vs:
                ts = [vi.timestamp for vi in vs]
                _mi = min(ts)
                _ma = max(ts)
                g.new_series(ts,
                             [vi.value for vi in vs],
                             yerror=ArrayDataSource([vi.error for vi in vs]),
                             marker_size=3,
                             fit=(iso.fit, 'SD'),
                             type='scatter', marker_color='red')

        if not _mi:
            _mi, _ma = self.timestamp - 86400, self.timestamp + 86400

        g.set_x_limits(_mi, _ma, pad='0.1')
        g.refresh()

        g.set_x_title('Time', plotid=0)
        g.edit_traits()

    def _load(self, an):
        self.analysis_uuid = an.uuid

        self.blank_changes = an.blank_changes
        self.fit_changes = an.fit_changes

        self.fit_selected = self.fit_changes[-1]

        self.blank_selected = next(([bi] for bi in self.blank_changes if bi.id == an.selected_blanks_id),
                                   self.blank_changes[-1:])

        self.timestamp = an.timestamp

    def traits_view(self):
        v = View(VSplit(UItem('blank_changes', editor=TabularEditor(adapter=BlankHistoryAdapter(),
                                                                    selected='blank_selected',
                                                                    refresh='refresh_needed',
                                                                    multi_select=True,
                                                                    editable=False)),
                        HGroup(
                            UItem('object.blank_selected_.isotopes', editor=TabularEditor(adapter=IsotopeBlankAdapter(),
                                                                                          refresh='refresh_needed',
                                                                                          selected='object.blank_selected_.selected',
                                                                                          editable=False)),
                            UItem('object.blank_selected_.selected.analyses',
                                  editor=TabularEditor(adapter=AnalysesAdapter(),
                                                       refresh='refresh_needed',
                                                       editable=False))),
                        label='Blanks'),
                 VSplit(
                     UItem('fit_changes', editor=TabularEditor(adapter=FitHistoryAdapter(),
                                                               selected='fit_selected',
                                                               editable=False)),
                     UItem('object.fit_selected.fits', editor=TabularEditor(adapter=FitAdapter(),
                                                                            editable=False)),
                     label='Iso. Fits'),
                 handler=HistoryHandler())
        return v

# ============= EOF =============================================

