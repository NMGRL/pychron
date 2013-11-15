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
from traits.api import List, Any, Event, Unicode
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.database.isotope_database_manager import IsotopeDatabaseManager


class Experimentable(IsotopeDatabaseManager):
    experiment_queues = List
    experiment_queue = Any

    text = None
    text_hash = None
    path = Unicode
    update_needed = Event
    add_queues_flag = Event

    def _get_all_automated_runs(self):
        return (ai for ei in self.experiment_queues
                    for ai in ei.automated_runs
                        if ai.executable)

    def _reload_from_disk(self):
#        if not self._alive:


        ts = self._parse_experiment_file(self.path)

        nl = len(ts)
        ol = len(self.experiment_queues)
        if nl < ol:
            self.experiment_queues = self.experiment_queues[:nl]
        elif nl > ol:
            self.add_queues_flag = nl - ol

        for ei, ti in zip(self.experiment_queues, ts):
#                ei._cached_runs = None
            ei.load(ti)

        self.update_needed = True
#        self._update(all_info=True)

    def _update(self, *args, **kw):
        pass

#     def _check_for_file_mods(self):
#         path = self.path
#         if path:
#             with open(path, 'r') as f:
#                 diskhash = hashlib.sha1(f.read()).hexdigest()
#             return self.text_hash != diskhash

    def _parse_experiment_file(self, path):
        with open(path, 'r') as f:
            ts = []
            tis = []
            a = ''
            for l in f:
                a += l
                if l.startswith('*' * 80):
                    ts.append(''.join(tis))
                    tis = []
                    continue

                tis.append(l)
            ts.append(''.join(tis))
#             self.text_hash = hashlib.sha1(a).hexdigest()
#             self.text = a
            return ts

#     def _path_changed(self):
#         if os.path.isfile(self.path):
#             with open(self.path, 'r') as fp:
#                 a = fp.read()
#                 self.text_hash = hashlib.sha1(a).hexdigest()
#                 self.text = a

#============= EOF =============================================
