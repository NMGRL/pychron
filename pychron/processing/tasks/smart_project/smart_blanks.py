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
from traits.api import Instance
#============= standard library imports ========================
import time
from datetime import timedelta
#============= local library imports  ==========================
from pychron.core.helpers.filetools import unique_path
from pychron.processing.tasks.smart_project.blanks_pdf_writer import BlanksPDFWrtier
from pychron.processing.tasks.smart_project.base_smarter import BaseSmarter

class SmartBlanks(BaseSmarter):
    editor = Instance('pychron.processing.tasks.blanks_editor.BlanksEditor')

    def simple_fit_blanks(self, n, ans, kind, dry_run):
        '''
            ans: analysis generator
            fit with preceding or bracketing
        '''
        man = self.processor
        if kind == 'preceding':
            func = man.preceding_blank_correct

        fn = float(n)
        st = time.time()
        for i, ai in enumerate(ans):
            func(ai)
            if i and i % 10 == 0:
                p = i / fn * 100

                et = time.time() - st
                ed = n * et / float(i)
                er = (ed - et) / 60.

                self.info('applying blank {:04n}/{:04n} ({:0.2f}%) estimated remain {:0.1f} (mins)'.format(i, n, p, er))
                if dry_run:
                    man.db.sess.rollback()
                else:
                    self.info('committing changes')
                    man.db.sess.commit()

    def interpolate_blanks(self, n, ans, fits, root, save_figure, with_table):
        func = self._do_fit_blanks  # (gs, fits, atype, root, save_figure, with_table)
        args = (fits, 'unkown', root, save_figure, with_table)

        self._block_analyses(n, ans, func, args)


    def _do_fit_blanks(self, gs, fits, atype, root,
                       save_figure, with_table):
        '''
            fit this block of analyses
        '''
        start, end = gs[0].analysis_timestamp, gs[-1].analysis_timestamp

        ds = timedelta(minutes=59)
        atypes = ('blank_{}'.format(atype),)

        blanks = self._get_analysis_date_range(start - ds, end + ds, atypes)
        if blanks:
            man = self.processor
            blanks = man.make_analyses(blanks)
            gs = man.make_analyses(gs)
            man.load_analyses(gs, show_progress=False)
            man.load_analyses(blanks, show_progress=False)

            refiso = gs[0]

            ae = self.editor
            ae.tool.load_fits(refiso.isotope_keys[:],
                                refiso.isotope_fits
                                )
            fkeys = fits.keys()
            for fi in ae.tool.fits:
                if fi.name in fkeys:
                    fi.trait_set(show=True, fit=fits[fi.name], trait_change_notify=False)

            ae.unknowns = gs
            ae.references = blanks
            ae.rebuild_graph()

            if save_figure:
                p, _ = unique_path(root, base=refiso.record_id,
                                   extension='.pdf')
                if with_table:
                    writer = BlanksPDFWrtier()
                    writer.build(p, ae.component, gs, blanks)
                else:
                    ae.graph.save_pdf(p)
#============= EOF =============================================
