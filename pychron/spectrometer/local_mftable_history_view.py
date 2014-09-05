# ===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import HasTraits, Float, List
from traitsui.api import View, UItem, VGroup, HSplit, TabularEditor
from traitsui.tabular_adapter import TabularAdapter
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.git_archive.history import GitArchiveHistory, GitArchiveHistoryView, \
    left_group, right_group, DiffView


class ItemAdapter(TabularAdapter):
    pass


class FieldItem(HasTraits):
    pass


class MFTableDiffView(DiffView):
    diff_items = List

    def __init__(self, *args, **kw):
        super(MFTableDiffView, self).__init__(*args, **kw)
        self._load_diff()

    def _load_diff(self):
        lkeys, lvalues = self._parse_txt(self.left)
        rkeys, rvalues = self._parse_txt(self.right)

        self.item_adapter = ItemAdapter()
        if lkeys == rkeys:
            cols = [(v, v) for v in lkeys]
            self.item_adapter.columns = cols

            for lv in lvalues:
                iso = lv[0]
                rv = next((ri for ri in rvalues if ri[0] == iso))
                d = FieldItem(iso=iso)
                for i, k in enumerate(lkeys[1:]):
                    dv = float(lv[i + 1]) - float(rv[i + 1])
                    d.add_trait(k, Float(dv))

                self.diff_items.append(d)

    def _parse_txt(self, txt):
        lines = txt.split('\n')
        keys = lines[0].split(',')
        data = [line.split(',') for line in lines[1:] if line]
        return keys, data

    def traits_view(self):
        v = View(VGroup(HSplit(left_group(), right_group()),
                        UItem('diff_items', editor=TabularEditor(editable=False,
                                                                 adapter=self.item_adapter))),
                 title='Diff',
                 width=900,
                 buttons=['OK'],
                 kind='livemodal',
                 resizable=True)
        return v


class LocalMFTableHistory(GitArchiveHistory):
    diff_klass = MFTableDiffView


class LocalMFTableHistoryView(GitArchiveHistoryView):
    pass


# if __name__ == '__main__':
#     r = '/Users/ross/Sandbox/gitarchive'
#     gh = LocalMFTableHistory(r, '/Users/ross/Sandbox/ga_test.txt')
#
#     gh.load_history('ga_test.txt')
#
#     gh.selected = [gh.items[5], gh.items[6]]
#     gh._diff_button_fired()
#     # ghv = LocalMFTableHistoryView(model=gh)
#     # ghv.configure_traits(kind='livemodal')
#============= EOF =============================================



