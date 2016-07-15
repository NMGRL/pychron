# ===============================================================================
# Copyright 2016 ross
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
from traits.api import Str, List
# ============= standard library imports ========================
import yaml
import re
import os
# ============= local library imports  ==========================
from pychron.core.progress import progress_loader
from pychron.dvc.dvc_database import DVCDatabase
from pychron.loggable import Loggable
from pychron.paths import paths

REGEX = re.compile(r'^(?P<keyword>[spimlt])(?P<comp>(:=)|:)(?P<term>[\w-]*)$')


class SearchParser:
    def parse(self, s):
        """
        convert search string into a search dictionary for easy use with sqlalchemy

        examples:

        s: FC-2
        find all analyses LIKE FC-2

        s:= FC-2
        find all analyses = FC-2

        multiple keywords can be searched at once. separate each search with ;

        s:=FC-2;i:=Ross

        search keywords
        ---------------
        s => Sample
        p => Project
        i => Principal Investigator
        m => Material
        l => Labnumber/identifier
        t => Analysis type

        :param s:
        :return:
        """

        queries = []
        for subsearch in s.split(';'):
            match = self._match(subsearch)
            if match:
                queries.append(match)

        return queries

    def _match(self, s):
        match = REGEX.match(s)
        if match:
            k = match.group('keyword')
            c = match.group('comp')
            t = match.group('term')
            return k, c, t


class Searcher(Loggable):
    search_entry = Str
    search_entries = List
    db = None
    _parser = None

    def __init__(self, *args, **kw):
        super(Searcher, self).__init__(*args, **kw)
        self._parser = SearchParser()
        self._load_entries()

    def search(self):
        terms = self._parser.parse(self.search_entry)
        self.debug('{} => {}'.format(self.search_entry, terms))
        if terms:
            results = self.db.search_analyses(terms, limit=self.analysis_table.limit)
            results = self._make_records(results)
            self.analysis_table.set_analyses(results)

    def add_search_entry(self):
        p = paths.hidden_path('search_entries')
        with open(p, 'w') as wfile:
            if self.search_entry not in self.search_entries:
                self.search_entries.append(self.search_entry)
                yaml.dump([str(s) for s in self.search_entries], wfile)

    def _make_records(self, ans):
        def func(xi, prog, i, n):
            if prog:
                # if prog and i % 25 == 0:
                prog.change_message('Loading {}'.format(xi.record_id))
            return xi.record_views

        return progress_loader(ans, func, threshold=25, step=25)

    def _load_entries(self):
        p = paths.hidden_path('search_entries')
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                self.search_entries = yaml.load(rfile)

    def _search_entry_changed(self):
        self.search()


if __name__ == '__main__':
    db = DVCDatabase(bind=False, kind='mysql', host='localhost', username='root', name='pychrondvc_dev',
                     password='Argon')
    db.connect()

    # s = SearchParser(db=db)
    # s.parse('s:FC-2')
    # s.parse('s:=FC-2')
    # s.parse('s=FC-2')
    s = Searcher(db=db)
    s.search_entry = 's:FC-2'
    s.search()
# ============= EOF =============================================
