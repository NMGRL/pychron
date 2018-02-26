# ===============================================================================
# Copyright 2017 ross
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
from traits.api import List, Instance, Any, Str

from pychron.core.fuzzyfinder import fuzzyfinder
from pychron.envisage.browser.record_views import SampleRecordView
from pychron.loggable import Loggable


class SimpleIdentifierManager(Loggable):
    items = List
    dvc = Instance('pychron.dvc.dvc.DVC')

    project_filter = Str
    selected_project = Any
    projects = List
    oprojects = List

    selected_sample = Any
    samples = List
    factory = None

    def activated(self):
        self.debug('activated')
        self.dvc.create_session()

        self.items = self.dvc.db.get_simple_identifiers()
        self.oprojects = self.dvc.db.get_project_names()
        self.projects = self.oprojects

    def prepare_destroy(self):
        self.debug('prepare destroy')
        self.dvc.close_session()

    def set_identifier(self):
        self.debug('set identifier {}'.format(self.selected_sample))
        identifier = self.dvc.get_simple_identifier(self.selected_sample.id)
        if not identifier:
            self.debug('no identifier. adding simple identifier for {}'.format(self.selected_sample))
            self.dvc.add_simple_identifier(self.selected_sample.id)
            self.items = self.dvc.db.get_simple_identifiers()
        else:
            self.information_dialog('"{}" already has an identifier "{}"'.format(self.selected_sample,
                                                                                 identifier.identifier))

    # handlers
    def _selected_sample_changed(self, new):
        if new and self.factory:
            identifiers = [i.identifier for i in self.dvc.db.get_sample_simple_identifiers(new.id)]
            self.factory.set_identifiers(identifiers)
            self.factory.labnumber = new.identifier

    def _project_filter_changed(self, new):
        if new:
            self.projects = fuzzyfinder(new, self.oprojects)
        else:
            self.projects = self.oprojects

    def _selected_project_changed(self):
        self.samples = [SampleRecordView(ni) for ni in self.dvc.db.get_samples(self.selected_project)]

# ============= EOF =============================================
