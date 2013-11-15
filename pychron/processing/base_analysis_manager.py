#===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import HasTraits, List, Instance
#============= standard library imports ========================
#============= local library imports  ==========================

from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.paths import paths
from pychron.processing.window import Window
from pychron.processing.search.selector_manager import SelectorManager
from pychron.processing.search.search_manager import SearchManager
from pychron.processing.analysis import Marker, Analysis
from pychron.database.records.isotope_record import IsotopeRecord

class BaseAnalysisManager(IsotopeDatabaseManager):
    _window_count = 0
    figures = List

    selector_manager = Instance(SelectorManager, ())
    search_manager = Instance(SearchManager, ())

    def edit_analyses(self):
        sm = self.selector_manager
        info = sm.edit_traits(kind='livemodal')
        if info.result:
            analyses = self._get_analyses()
            if analyses:
                self._load_analyses(analyses)
                title = self._make_title(analyses)

                plotter = self._get_active_plotter()
                if plotter:
                    plotter.options['title'] = title
                    plotter.build(analyses, new_container=False)

                table = self._get_active_table()
                if table:
                    table.set_title(title)
                    table.analyses = analyses

    def ideogram(self, analyses=None):
        options = self._get_options('ideogram')
        if options:
            return self._new_figure('ideogram', options, analyses)

    def _get_options(self, name):
#        pom = getattr(self, '{}_options_manager'.format(name))

        if name == 'ideogram':
            from pychron.processing.plotter_options_manager import IdeogramOptionsManager
            pom = IdeogramOptionsManager()

        info = pom.edit_traits(kind='livemodal')
        if info.result:
            return pom.plotter_options

    def _gather_data(self, data_type='database'):
        '''
            open a data selector view
            
            by default use a db connection
            returns database for database entry
                    path for data_file
                    
        '''
#        return True
        if data_type == 'database':
            d = self.selector_manager
            if self.db.connect():
                info = d.edit_traits(kind='livemodal')
                if info.result:
                    return True
        elif data_type == 'data_file':
            if self.confirmation_dialog('''Select a file with the following format. (Include first Line)
            
identifier, age, error
1000,10.0, 0.1
1001,10.0, 0.1
g
2001,10.0, 0.1
2002,10.0, 0.1
Use 'g' to separate groups''', title='Select a DataFile'):
                p = self.open_file_dialog(default_directory=paths.data_dir)
                return p

    def _new_figure(self, name, options, analyses):
        if analyses is None:
            use_db_or_path = self._gather_data(options)
            if use_db_or_path is not None:
                analyses = self._get_analyses(use_db_or_path)
                if analyses:
                    self._load_analyses(analyses)
        else:
            self.selector_manager.selected_records = analyses

        if analyses:
            if options and options.title != '' and not options.auto_generate_title:
                title = options.title
            else:
                title = self._make_title(analyses)

            func = getattr(self, '_display_{}'.format(name))
            return func(analyses, options, title, show_table=options.data_type == 'database'
#                 data_type=options.data_type
                 )

    def _display_ideogram(self, analyses, options, title, show_table):
        rr = self._ideogram(analyses, options,
                            title=title
                            )
        if rr:
            g, ideo = rr
            return self._display_figure_and_table(g, ideo, analyses, title, show_table)

    def _display_figure_and_table(self, g, fig, ans, title, show_table):
        table = None
        if show_table:
            table = self._display_tabular_data(ans, title)

        self._open_figure(g, fig, table=table)
        if table is not None:
            g.associated_windows.append(table)

        return fig
    def _ideogram(self, analyses,
                  plotter_options,
#                  probability_curve_kind='cumulative',
#                  mean_calculation_kind='weighted_mean',
#                  aux_plots=None,
                  title=None,
#                  xtick_font=None,
#                  xtitle_font=None,
#                  ytick_font=None,
#                  ytitle_font=None,
                  data_label_font=None,
                  metadata_label_font=None,
                  highlight_omitted=True,
                  display_mean_indicator=True,
                  display_mean_text=True
                  ):
        '''
        '''
        from pychron.processing.plotters.ideogram import Ideogram

        g = self._window_factory()
        p = Ideogram(db=self.db,
                     processing_manager=self,
                     probability_curve_kind=plotter_options.probability_curve_kind,
                     mean_calculation_kind=plotter_options.mean_calculation_kind
                     )

#        ps = self._build_aux_plots(plotter_options.get_aux_plots())
        options = dict(
#                       aux_plots=ps,
#                       use_centered_range=plotter_options.use_centered_range,
#                       centered_range=plotter_options.centered_range,
#                       xmin=plotter_options.xmin,
#                       xmax=plotter_options.xmax,
#                       xtitle_font=xtitle_font,
#                       xtick_font=xtick_font,
#                       ytitle_font=ytitle_font,
#                       ytick_font=ytick_font,
                       data_label_font=data_label_font,
                       metadata_label_font=metadata_label_font,
                       title=title,
                       display_mean_text=display_mean_text,
                       display_mean_indicator=display_mean_indicator,
                       )

        gideo = p.build(analyses, options=options, plotter_options=plotter_options)
        if gideo:
            gideo, _plots = gideo
            g.container.add(gideo)

            if highlight_omitted:
                ta = sorted(analyses, key=lambda x:x.age)
                # find omitted ans
                sel = [i for i, ai in enumerate(ta) if ai.status != 0]
                p.set_excluded_points(sel, 0)

            return g, p

    def _get_analyses(self, use_db_or_path=True):
        if isinstance(use_db_or_path, bool):
            ps = self.selector_manager
#            db = self.db
#            def factory(pi):
#                rec = IsotopeRecord(_dbrecord=db.get_analysis_uuid(pi.uuid),
#                                    graph_id=pi.graph_id,
#                                    group_id=pi.group_id)
#                return Analysis(isotope_record=rec)

            ans = [ri for ri in ps.selected_records
                                if not isinstance(ri, Marker)]
        else:
            ans = self._parse_data_file(use_db_or_path)
            if isinstance(ans, str):
                self.warning_dialog('Invalid file. {}'.format(ans))
                return

        return ans

#===============================================================================
# active
#===============================================================================
    def _get_active_window(self):
        return self._get_active_item(0)

    def _get_active_plotter(self):
        return self._get_active_item(1)

    def _get_active_table(self):
        return self._get_active_item(2)

    def _get_active_item(self, ind):
        args = next(((win, plotter, table) for win, plotter, table in self.figures
                       if win.IsActive()), None)
        if args:
            return args[ind]

#===============================================================================
# window
#===============================================================================
    def _open_figure(self, fig, obj=None, table=None):
        self._set_window_xy(fig)
        self.figures.append((fig, obj, table))
        self.open_view(fig)

    def _set_window_xy(self, obj):
        x = 50
        y = 25
        xoff = 25
        yoff = 25
        obj.window_x = x + xoff * self._window_count
        obj.window_y = y + yoff * self._window_count
        self._window_count += 1

    def _window_factory(self):
#        w = self.get_parameter('window', 'width', default=500)
#        h = self.get_parameter('window', 'height', default=600)
#        x = self.get_parameter('window', 'x', default=20)
#        y = self.get_parameter('window', 'y', default=20)
        x, y, w, h = 20, 20, 500, 600
        g = Window(
                   manager=self,
                   window_width=w,
                   window_height=h,
                   window_x=x, window_y=y
                   )
        self.window = g
        return g

#===============================================================================
# title
#===============================================================================
    def _make_title(self, analyses):
        def make_bounds(gi, sep='-'):
            if len(gi) > 1:
                m = '{}{}{}'.format(gi[0], sep, gi[-1])
            else:
                m = '{}'.format(gi[0])

            return m

        def make_step_bounds(si):
            if not si:
                return
            grps = []
            a = si[0]
            pa = si[1]
            cgrp = [pa]
            for xi in si[2:]:
                if ord(pa) + 1 == ord(xi):
                    cgrp.append(xi)
                else:
                    grps.append(cgrp)
                    cgrp = [xi]
                pa = xi

            grps.append(cgrp)
            return ','.join(['{}{}'.format(a, make_bounds(gi, sep='...')) for gi in grps])

        def _make_group_title(ans):
            lns = dict()
            for ai in ans:
    #            v = '{}{}'.format(ai.aliquot, ai.step)
                v = (ai.aliquot, ai.step)
                if ai.labnumber in lns:
                    lns[ai.labnumber].append(v)
                else:
                    lns[ai.labnumber] = [v]

            skeys = sorted(lns.keys())
            grps = []
            for si in skeys:
                als = lns[si]
                sals = sorted(als, key=lambda x: x[0])
                aliquots, steps = zip(*sals)

                pa = aliquots[0]
                ggrps = []
                cgrp = [pa]
                sgrp = []
                sgrps = []

                for xi, sti in zip(aliquots[1:], steps[1:]):
                    # handle analyses with steps
                    if sti != '':
                        if not sgrp:
                            sgrp.append(xi)
                        elif sgrp[0] != xi:
                            sgrps.append(sgrp)
                            sgrp = [xi]
                        sgrp.append(sti)
                    else:
                        if sgrp:
                            sgrps.append(sgrp)
                            sgrp = []

                        if pa + 1 == xi:
                            cgrp.append(xi)
                        else:
                            ggrps.append(cgrp)
                            cgrp = [xi]

                    pa = xi

                sgrps.append(sgrp)
                ggrps.append(cgrp)
                fs = [make_bounds(gi) for gi in ggrps]

                if sgrps[0]:
                    # handle steps
                    pa = sgrps[0][0]
                    ggrps = []
                    cgrp = [sgrps[0]]
                    for sgi in sgrps[1:]:
                        if pa + 1 == sgi[0]:
                            cgrp.append(sgi)
                        else:
                            grps.append(cgrp)
                            cgrp = [sgi]
                        pa = sgi[0]
                    ggrps.append(cgrp)
                    ss = ['{}-{}'.format(make_step_bounds(gi[0]),
                            make_step_bounds(gi[-1])) for gi in ggrps]
                    fs.extend(ss)

                als = ','.join(fs)

                grps.append('{}-({})'.format(si, als))

            return ', '.join(grps)

        group_ids = list(set([a.group_id for a in analyses]))
        gtitles = []
        for gid in group_ids:
            anss = [ai for ai in analyses if ai.group_id == gid]
            gtitles.append(_make_group_title(anss))

        return ', '.join(gtitles)


#===============================================================================
# defaults
#===============================================================================
    def _selector_manager_default(self):
        db = self.db
        d = SelectorManager(db=db)
#        if not db.connected:
#            db.connect()

#        d.select_labnumber([61541])
#        d.select_labnumber([22233])
        return d

    def _search_manager_default(self):
        db = self.db
        d = SearchManager(db=db)
        if not db.connected:
            db.connect()
        return d
#============= EOF =============================================
