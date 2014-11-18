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
from traits.api import Any, on_trait_change, DelegatesTo, List
from pyface.tasks.task_layout import TaskLayout, HSplitter

from pychron.processing.tasks.analysis_edit.analysis_edit_task import AnalysisEditTask
from pychron.processing.tasks.browser.browser_task import BaseBrowserTask
from pychron.processing.tasks.browser.util import browser_pane_item
from pychron.processing.tasks.repository.panes import RepositoryPane
from pychron.processing.repository.geochron_repo import GeochronRepository
from pychron.processing.repository.igsn import IGSN



#============= standard library imports ========================
#============= local library imports  ==========================

class RepositoryTask(AnalysisEditTask):
    name = 'Repository'
    repository = Any
    igsn = Any

    igsn_enabled = DelegatesTo('igsn', prefix='enabled')
    repo_enabled = DelegatesTo('repository', prefix='enabled')
    auto_show_unknowns_pane = False

    tool_bars = List

    def _selected_projects_changed(self, old, new):
        project = ''
        if new:
            project = new[0].name

        self.igsn.project = project
        BaseBrowserTask._selected_projects_changed(self, old, new)

    def _selected_samples_changed(self, new):
        sample = ''
        if new:
            sample = new[0].name
        self.igsn.sample = sample

    def _repository_default(self):
        return GeochronRepository()

    def _igsn_default(self):
        return IGSN()

    def create_central_pane(self):
        return RepositoryPane(model=self)

    def create_dock_panes(self):
        #ps = AnalysisEditTask.create_dock_panes(self)
        #ps.extend([BrowserPane(model=self)])
        ps = [self._create_browser_pane(analyses_defined='0')]
        return ps

    def _save_to_db(self):
        """
            save the sample igsn to the database
        """
        db = self.manager.db
        with db.session_ctx():
            s = self.selected_samples
            p = self.selected_projects
            dbsample = db.get_sample(s.name, project=p.name)
            if dbsample is not None:
                dbsample.igsn = s.igsn
            else:
                msg = 'Sample: {}, Project: {} \
                not found in database'.format(s.name, p.name)
                self.warning_dialog(msg)

        self.info('Sample: {}, Project: {}. IGSN set to {}'.format(s.name,
                                                                   p.name,
                                                                   s.igsn))

    #===============================================================================
    # handlers
    #===============================================================================
    @on_trait_change('igsn:new_igsn')
    def _new_igsn(self, new):
        """
            associate the new igsn with the current sample and save to the
            database
        """
        sample = self.igsn.sample
        project = self.igsn.project
        self.debug('Retrieved new IGSN:{} for project: {} sample: {}'.format(new, sample, project))

        self.selected_samples.igsn = new
        self._save_to_db()

    #     @on_trait_change('igsn:[sample, username, password]')
    #     def _update_igsn(self):
    #         self.igsn_enabled = all([getattr(self.igsn, a)
    #                                  for a in ('sample', 'username', 'password')])
    #
    #     @on_trait_change('repository:enabl')
    #     def _update_repo(self):
    #         self.repo_enabled = all([getattr(self.repository, a)
    #                                  for a in ('username', 'password')])
    #===============================================================================
    # defaults
    #===============================================================================
    def _default_layout_default(self):
        return TaskLayout(id='pychron.repository',
                          left=HSplitter(
                              browser_pane_item(),
                          )
                          #                           left=HSplitter(

                          #                                     PaneItem('pychron.browser'),
                          #                                     Splitter(
                          #                                          Tabbed(
                          #                                                 PaneItem('pychron.processing.unknowns'),
                          # #                                                 PaneItem('pychron.processing.figures.plotter_options')
                          #                                                 ),
                          # #                                          Tabbed(
                          # #                                                 PaneItem('pychron.processing.controls'),
                          # #                                                 PaneItem('pychron.processing.editor'),
                          # #                                                 ),
                          #                                          orientation='vertical'
                          #                                          )
                          #                                     ),

        )

        #============= EOF =============================================
