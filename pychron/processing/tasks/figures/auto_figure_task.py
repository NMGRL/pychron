#===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import on_trait_change, Instance, Dict, Bool, Str, Int
from pyface.tasks.task_layout import TaskLayout, Splitter, PaneItem, Tabbed
from apptools.preferences.preference_binding import bind_preference

from pychron.processing.tasks.figures.panes import PlotterOptionsPane
from pychron.processing.tasks.figures.figure_task import FigureTask
from pychron.processing.tasks.figures.auto_figure_panes import AutoFigureControlPane
from pychron.messaging.notify.subscriber import Subscriber
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.processing.tasks.figures.editors.series_editor import AutoSeriesEditor
from pychron.processing.tasks.figures.editors.spectrum_editor import AutoSpectrumEditor
from pychron.processing.tasks.figures.editors.ideogram_editor import AutoIdeogramEditor

# from pychron.processing.tasks.analysis_edit.plot_editor_pane import EditorPane
#============= standard library imports ========================
#============= local library imports  ==========================

class AutoFigureTask(FigureTask):
    name = 'AutoFigure'
    id = 'pychron.processing.auto_figure'
    plotter_options_pane = Instance(PlotterOptionsPane)

    _cached_samples = None
    _cached = Dict

    use_single_ideogram = Bool(True)
    attached = False

    host = Str('129.138.12.141')
    port = Int(8101)

    def __init__(self, *args, **kw):
        super(AutoFigureTask, self).__init__(*args, **kw)

        bind_preference(self, 'host', 'pychron.auto_figure.host')
        bind_preference(self, 'port', 'pychron.auto_figure.port')


    def activated(self):
        if not self.attached:
            sub_str = 'RunAdded'
            self.info('starting subscription to {}:{} "{}"'.format(self.host, self.port, sub_str))
            sub = Subscriber(host=self.host,
                             port=self.port)
            sub.connect()
            sub.subscribe(sub_str)
            sub.listen(self.sub_refresh_plots)

            self.attached = True

    def sub_refresh_plots(self, last_run):
        self.manager.db.reset()
        invoke_in_main_thread(self.refresh_plots, last_run)

    def refresh_plots(self, last_run):
        '''
            if last run is part of a step heat experiment
            plot spectrum for list sample/aliquot
            
            if last run is blank, air, cocktail 
            plot a series
        '''
        if isinstance(last_run, (str, unicode)):
            args = self._get_args(last_run)
            self.debug('{} {}'.format(args, last_run))
            if args:
                ln, at, sample, eg, al, ms, ed = args
            else:
                return

        else:
            spec = last_run.spec
            ln = spec.labnumber
            at = spec.analysis_type
            sample = spec.sample
            eg = spec.extract_group
            al = spec.aliquot
            ms = spec.mass_spectrometer
            ed = spec.extract_device

        if at == 'unknown':
            self._refresh_unknown(ln, sample, eg, al)
        else:
            self._refresh_series(ln, ms, ed, at)

    def _get_args(self, uuid):
        an = self.manager.db.get_analysis(uuid, key='uuid')
        if an is not None:
            ln = an.labnumber.identifier

            at = an.measurement.analysis_type.name

            sample = ''
            if an.labnumber.sample:
                sample = an.labnumber.sample.name
                #
            eg = an.step
            al = an.aliquot
            ms = an.measurement.mass_spectrometer.name
            if an.extraction:
                ed = an.extraction.extraction_device.name
            else:
                ed = ''

            return ln, at, sample, eg, al, ms, ed


    def _refresh_unknown(self, ln, sample, extract_group, aliquot):
        if sample:
            if extract_group:
                self.plot_sample_spectrum(sample, aliquot)
            else:
                self.plot_sample_ideogram(ln, sample)

    def _refresh_series(self, ln, ms, ed, at):
        editor = self._get_editor(AutoSeriesEditor)
        if editor:
            afc = editor.auto_figure_control
            days, hours = afc.days, afc.hours
        else:
            days, hours = 1, 0
        self.plot_series(ln, at, ms, ed,
                         days=days, hours=hours)

    def _unique_analyses(self, ans):
        if ans:
            items = self.unknowns_pane.items
            if items:
                uuids = [ai.uuid for ai in items]
                ans = [ui for ui in ans if ui.uuid not in uuids]
        return ans

    def plot_series(self, ln=None, at=None, ms=None, ed=None, **kw):

        if ln is None:
            ln = self._cached['ln']
        if at is None:
            at = self._cached['analysis_type']
        if ms is None:
            ms = self._cached['ms']
        if ed is None:
            ed = self._cached['ed']

        self._cached['ln'] = ln
        self._cached['analysis_type'] = at
        self._cached['ms'] = ms
        self._cached['ed'] = ed

        klass = AutoSeriesEditor
        editor = self._get_editor(klass, labnumber=ln)
        if editor:
            unks = self.manager.load_series(at, ms, ed,
                                            **kw)
            nunks = self._unique_analyses(unks)
            if nunks:
                self.unknowns_pane.items.extend(nunks)

        else:
            unks = self.manager.load_series(at, ms, ed,
                                            **kw)
            if unks:
            #                 self.manager.load_analyses(unks)
                self.new_series(unks, klass,
                                #                                add_baseline_fits=True,
                                #                                add_derivate_fits=True,
                                name='Series {}'.format(ln))
                #
                editor = self.active_editor
                tool = editor.tool

                ref = unks[0]
                tool.load_baseline_fits(ref.isotope_keys)
                tool.add_peak_center_fit()
                tool.add_derivated_fits(ref.isotope_keys)

                self.active_editor.labnumber = ln
                self.active_editor.show_series('Ar40')

    def _get_editor(self, klass, **kw):

        def test(editor):
            if isinstance(editor, klass):
                for k, v in kw.iteritems():
                    if hasattr(editor, k):
                        if getattr(editor, k) != v:
                            break
                    else:
                        break
                else:
                    return True
                    #                         getattr(editor, k)==v


        return next((editor for editor in self.editor_area.editors
                     if test(editor)), None)

    def plot_sample_spectrum(self, sample, aliquot):
        self.debug('auto plot sample spectrum sample={} aliquot={}'.format(sample, aliquot))
        klass = AutoSpectrumEditor
        editor = self._get_editor(klass)
        if editor:
            unks = self.manager.load_sample_analyses(sample, aliquot)
            nunks = self._unique_analyses(unks)
            if nunks:
                self.unknowns_pane.items.extend(nunks)

        else:
            unks = self.manager.load_sample_analyses(sample, aliquot)
            #             self.manager.load_analyses(unks)
            self.new_spectrum(unks, klass)
        self.group_by_aliquot()

    def plot_sample_ideogram(self, ln, sample):
        self.debug('auto plot sample ideogram lab={}'.format(sample))
        klass = AutoIdeogramEditor
        if self.use_single_ideogram:
            editor = self._get_editor(klass)
        else:
        #             editor = self._get_editor(klass, labnumber=labnumber)
            editor = self._get_editor(klass, sample=sample)

        if editor:

            unks = self.manager.load_sample_analyses(ln, sample)
            nunks = self._unique_analyses(unks)
            if nunks:
                self.unknowns_pane.items.extend(nunks)

        else:
            unks = self.manager.load_sample_analyses(ln, sample)
            #             self.manager.load_analyses(unks)
            #             self.new_ideogram(unks, klass, name='Ideo. {}'.format(labnumber))
            self.new_ideogram(unks, klass, name='Ideo. {}'.format(sample),
                              plotter_kw=dict(color_map_analysis_number=False)
            )
            self.active_editor.sample = sample

        if self.use_single_ideogram:
            if self.active_editor.auto_figure_control.group_by_labnumber:
                self.group_by_labnumber()

            if self.active_editor.auto_figure_control.group_by_aliquot:
                self.group_by_aliquot()

    def create_dock_panes(self):
        panes = super(AutoFigureTask, self).create_dock_panes()

        self.auto_figure_control_pane = AutoFigureControlPane()
        return panes + [self.auto_figure_control_pane]

    #         self.plotter_options_pane = PlotterOptionsPane()
    #         return panes + [self.plotter_options_pane,
    #                         ]

    def _active_editor_changed(self):
        if self.active_editor:
            self.auto_figure_control_pane.auto_control = self.active_editor.auto_figure_control

        super(AutoFigureTask, self)._active_editor_changed()

    @on_trait_change('''active_editor:auto_figure_control:[group_by_aliquot,
group_by_labnumber]''')
    def _update_group_by_aliquot(self, name, new):
        if new:
            if name == 'group_by_aliquot':
                self.group_by_aliquot()
            else:
                self.group_by_labnumber()
        else:
            self.clear_grouping()

    @on_trait_change('active_editor:auto_figure_control:[hours, days]')
    def _update_series_limits(self, name, new):
        self.unknowns_pane.items = []
        self.plot_series(**{name: new})

    #     @on_trait_change('active_editor:plotter:recall_event')
    #     def _recall(self, new):
    #         print new

    @on_trait_change('plotter_options_pane:pom:plotter_options:[+, aux_plots:+]')
    def _options_update(self, name, new):
        if name == 'initialized':
            return

        self.active_editor.rebuild(refresh_data=False)

    #        po = self.plotter_options_pane.pom.plotter_options
    #        comp = self.active_editor.make_func(ans=ans, plotter_options=po)
    #        self.active_editor.component = comp


    def _default_layout_default(self):
        return TaskLayout(
            id='pychron.analysis_edit',
            left=Splitter(
                Tabbed(
                    PaneItem('pychron.analysis_edit.unknowns'),
                    PaneItem('pychron.processing.figures.plotter_options')
                ),
                Tabbed(
                    PaneItem('pychron.analysis_edit.controls'),
                    PaneItem('pychron.processing.editor'),
                    PaneItem('pychron.processing.auto_figure_controls')
                ),
                orientation='vertical'
            ),

            right=Splitter(
                PaneItem('pychron.search.query'),
                orientation='vertical'
            )
        )

        #============= EOF =============================================
