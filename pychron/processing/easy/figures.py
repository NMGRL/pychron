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

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.experiment.easy_parser import EasyParser
from pychron.helpers.filetools import unique_path
from pychron.processing.easy.base_easy import BaseEasy
from pychron.processing.tasks.figures.editors.ideogram_editor import IdeogramEditor


class EasyFigures(BaseEasy):
    def _save_fusion(self, editor, root, ident):
        p, _ = unique_path(root, '{}_fusion_figure'.format(ident), extension='.pdf')
        editor.save_file(p, title='Ar/Ar Data')

        p, _ = unique_path(root, '{}_fusion_figure'.format(ident), extension='.xls')
        editor.save_file(p, title='Ar/Ar Data')

    def make_figures(self):
        ep = EasyParser()
        root = self._make_root(ep)

        doc = ep.doc('figures')

        #make a figure for each labnumber
        projects = doc['projects']

        ieditor = IdeogramEditor(processor=self)
        options = doc['options']
        ieditor.plotter_options_manager.set_plotter_options(options['ideogram'])

        self._make(projects, root, ieditor, ieditor, 'Figure')


#============= EOF =============================================
