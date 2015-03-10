# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
# from traits.api import HasTraits
# ============= standard library imports ========================
import os
from datetime import datetime
import time

import yaml




# ============= local library imports  ==========================
from pychron.processing.tasks.analysis_edit.analysis_edit_task import AnalysisEditTask
from pychron.paths import paths, r_mkdir
from pychron.entry.tasks.importer import ImporterModel

# from pychron.database.orms.isotope_orm import meas_AnalysisTable, \
#     meas_MeasurementTable, gen_AnalysisTypeTable, irrad_IrradiationTable, \
#     irrad_LevelTable, gen_LabTable, irrad_PositionTable, \
#     gen_MassSpectrometerTable

from pychron.database.orms.isotope.meas import meas_AnalysisTable, meas_MeasurementTable
from pychron.database.orms.isotope.irrad import irrad_PositionTable, irrad_IrradiationTable, irrad_LevelTable
from pychron.database.orms.isotope.gen import gen_AnalysisTypeTable, gen_MassSpectrometerTable, gen_LabTable

from pychron.processing.tasks.blanks.blanks_editor import BlanksEditor
from pychron.core.ui.gui import invoke_in_main_thread
# from pychron.core.helpers.filetools import unique_path
# from pychron.processing.tasks.smart_project.blanks_pdf_writer import BlanksPDFWrtier
from pychron.processing.tasks.smart_project.smart_blanks import SmartBlanks
from pychron.processing.tasks.smart_project.smart_isotope_fits import SmartIsotopeFits
from pychron.processing.tasks.smart_project.smart_detector_intercalibration import SmartDetectorIntercalibration
from pychron.processing.tasks.detector_calibration.intercalibration_factor_editor import IntercalibrationFactorEditor
from pychron.processing.tasks.smart_project.smart_flux import SmartFlux


class SmartProjectTask(AnalysisEditTask):
    id = 'pychron.processing.smart_project'

    def process_project_file(self):

        p = os.path.join(paths.processed_dir, 'miller.yaml')
        with open(p, 'r') as rfile:
            md = yaml.load_all(rfile)

            setup = md.next()

            project = setup['project']

            meta = md.next()
            if setup['import_irradiations']:
                self._import_irradiations(meta)

            meta = md.next()
            if setup['fit_isotopes']:
                self._fit_isotopes(meta)
            if setup['fit_blanks']:
                self._fit_blanks(meta, project)
            if setup['fit_detector_intercalibrations']:
                self._fit_detector_intercalibrations(meta, project)
            if setup['fit_flux']:
                self._fit_flux(meta, project)

            meta = md.next()
            if setup['make_figures']:
                self._make_figures(meta, project)
            if setup['make_tables']:
                self._make_tables(meta, project)

                # ===============================================================================
                # import
                # ===============================================================================

    def _import_irradiations(self, meta):
        self.debug('importing analyses')

        if not self._set_destination(meta):
            self.warning('failed to set destination')
            return

        im = ImporterModel(db=self.manager.db)
        self._set_source(meta, im)

        self._set_importer(meta, im)

        if im.do_import(new_thread=False):
            self.debug('import finished')
        else:
            self.warning('import failed')

    def _make_import_selection(self, meta):
        s = [(irrad['name'], irrad['levels'].split(','))
             for irrad in meta['irradiations']]
        return s

    def _make_fit_selection(self, meta):
        s = [(irrad['name'], irrad['levels'].split(','))
             for irrad in meta['irradiations']]
        return s

    def _set_importer(self, meta, im):
        imports = meta['imports'][0]

        im.include_analyses = imports['atype'] == 'unknown'
        im.include_blanks = imports['blanks']
        im.include_airs = imports['airs']
        im.include_cocktails = imports['cocktails']

        im.import_kind = 'irradiation'

        im.selected = self._make_import_selection(meta)
        im.dry_run = imports['dry_run']

    def _set_destination(self, meta):
        try:
            dest = meta['destination']
        except KeyError:
            return

        db = self.manager.db
        db.name = dest['database']
        db.username = dest['username']
        db.password = dest['password']
        db.host = dest['host']
        return db.connect()

    def _set_source(self, meta, im):
        source = meta['source']
        dbconn_spec = im.importer.dbconn_spec
        dbconn_spec.database = source['database']
        dbconn_spec.username = source['username']
        dbconn_spec.password = source['password']
        dbconn_spec.host = source['host']

    # ===============================================================================
    # figures/tables
    # ===============================================================================
    def _make_figures(self, meta, project):
        '''
            figs: dict 
              keys: 
                type: str, name: str, samples: list
        '''
        figures = meta['figures']
        if figures:
            self._make_output_dir(figures[0]['output'], project)

            for fi in figures[1:]:
                self._make_figure(fi)

    def _make_tables(self, meta, project):
        '''
            tabs: dict 
              keys: 
                type: str, name: str, samples: list
        '''
        tables = meta['tables']
        if tables:
            self._make_output_dir(tables[0]['output'], project)
            for ti in tables[1:]:
                self._make_table(ti)

    def _make_figure(self, fdict):
        pass

    def _make_table(self, tdict):
        pass


    # ===============================================================================
    # fitting
    # ===============================================================================
    def _fit_isotopes(self, meta):
        fitting = meta['fitting']
        dry_run = fitting['dry_run']
        projects = fitting['projects']

        sf = SmartIsotopeFits(processor=self.manager)
        if meta.has_key('irradiations'):
            irradiations = self._make_fit_selection(meta)

            sf.fit_irradiations(irradiations, projects, dry_run)
            #             self._fit_irradiations(irradiations, projects, dry_run)

        if meta.has_key('date_range'):
            dr = meta['date_range']
            posts = dr['start'], dr['end']
            at = dr['atypes']
            start, end = map(self._convert_date_str, posts)

            sf.fit_date_range(start, end, at, dry_run)
            #             self._fit_date_range(start, end, at, dry_run)

    def _fit_blanks(self, meta, project):
        st = time.time()
        fm = meta['fit_blanks']
        root = None
        if fm['save_figure']:
            path = fm['output']
            root = self._make_output_dir(path, project)

        fitting = meta['fitting']
        projects = fitting['projects']
        dry_run = fitting['dry_run']
        irradiations = self._make_fit_selection(meta)

        f = meta['fit_blanks']
        atypes = f['atypes']
        with self.manager.db.session_ctx():
            n, ans = self._analysis_generator(irradiations, projects, atypes)
            interp = f['interpolate']
            sb = SmartBlanks(processor=self.manager)
            if interp is True:

                fits = f['fits']
                save_figure = f['save_figure']
                with_table = f['with_table']
                be = BlanksEditor(name='Blanks',
                                  auto_find=False,
                                  show_current=False)

                sb.editor = be
                invoke_in_main_thread(self._open_editor, be)
                time.sleep(1)

                sb.interpolate_blanks(n, ans, fits, root, save_figure, with_table)
                #             self._interpolate_blanks(n, ans, fits, root,
                #                                      save_figure, with_table)
            else:
                sb.simple_fit_blanks(n, ans, interp, dry_run)
                #             self._simple_fit_blanks(n, ans, interp, dry_run)

            self._finish_db_session(dry_run)
            self.info('fit blanks finished elapsed time {}'.format(time.time() - st))

    def _fit_detector_intercalibrations(self, meta, project):
        # make graphs
        f = meta['fit_detector_intercalibrations']

        root = None
        if f['save_figure']:
            path = f['output']
            root = self._make_output_dir(path, project)

        fitting = meta['fitting']
        projects = fitting['projects']
        dry_run = fitting['dry_run']

        irradiations = self._make_fit_selection(meta)
        reftype = f['reference_type']
        unktypes = f['unknown_types']
        ms = f['mass_spectrometers']

        n, ans = self._analysis_generator(irradiations, projects,
                                          unktypes, mass_spectrometers=ms)
        standard = f['standard']
        sdf = SmartDetectorIntercalibration(processor=self.manager,

        )
        if f.has_key('value') and f['value']:
            v, e = map(float, f['value'].split(','))
            for ai in ans:
                sdf.set_user_value(ai, v, e)
        else:
            fit = f['fit']
            save_figure = f['save_figure']
            with_table = f['with_table']
            be = IntercalibrationFactorEditor(name='IC Factor',
                                              auto_find=False,
                                              show_current=False,
                                              standard=standard
            )

            sdf.editor = be
            invoke_in_main_thread(self._open_editor, be)
            time.sleep(1)

            sdf.fit_detector_intercalibration(n, ans, fit, reftype, root,
                                              save_figure, with_table)


    def _fit_flux(self, meta, project):
        ff = meta['fit_flux']
        save_fig = ff['save_figure']
        if save_fig:
            path = ff['output']
            root = self._make_output_dir(path, project)

        sf = SmartFlux(processor=self.manager,
                       monitor_age=ff['age']
        )

        irrad, level = 'NM-251', 'H'
        ans = sf.fit_level(irrad, level)

        name = '{}{}'.format(irrad, level)
        task = self._open_ideogram_editor(ans, name)

        if save_fig:
        #             task.save(os.path.join(root, '{}.pdf'.format(name)))
            p = os.path.join(root, '{}.pdf'.format(name))
            if ff['with_table']:
                comp = task.active_editor.component
                sf.save(p, ans, comp)
                self.view_pdf(p)
            else:
                task.save(p)
                # ===============================================================================
                # utilities
                # ===============================================================================

    def _finish_db_session(self, dry_run):
        if dry_run:
            self.manager.db.sess.rollback()
        else:
            self.manager.db.sess.commit()

            #     def _gather_analyses_for_blank_fit(self, irradiations, projects):
            #         return self._labnumber_generator(irradiations, projects)

    def _analysis_generator(self, irradiations, projects, atypes,
                            mass_spectrometers=None):
        db = self.manager.db

        irrads = [irrad for irrad, _ in irradiations]
        levels = [level
                  for _, levels in irradiations
                  for level in levels
        ]
        sess = db.sess
        q = sess.query(meas_AnalysisTable)
        q = q.join(gen_LabTable)
        q = q.join(irrad_PositionTable)
        q = q.join(irrad_LevelTable)
        q = q.join(irrad_IrradiationTable)

        q = q.join(meas_MeasurementTable)
        if mass_spectrometers:
            q = q.join(gen_MassSpectrometerTable)

        q = q.join(gen_AnalysisTypeTable)

        q = q.filter(meas_AnalysisTable.status == 0)
        q = q.filter(gen_AnalysisTypeTable.name.in_(atypes))
        q = q.filter(irrad_LevelTable.name.in_(levels))
        q = q.filter(irrad_IrradiationTable.name.in_(irrads))
        if mass_spectrometers:
            q = q.filter(gen_MassSpectrometerTable.name.in_(mass_spectrometers))

        q = q.order_by(meas_AnalysisTable.analysis_timestamp.asc())

        def gen():
            for a in q:
                yield a

        return q.count(), gen()

    def _convert_date_str(self, c):
        c = c.replace('/', '-')
        if c.count('-') == 2:
            fmt = '%m-%d-%Y'
        elif c.count('-') == 1:
            fmt = '%m-%Y'
        else:
            fmt = '%Y'
        return datetime.strptime(c, fmt)

    def _make_output_dir(self, path, project):
        if path.startswith('./'):
            # assume relative to processed dir
            path = os.path.join(paths.processed_dir,
                                project,
                                path[2:])
            #             print path, project, paths.processed_dir
        r_mkdir(path)
        return path

# ============= EOF =============================================
