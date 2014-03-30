#===============================================================================
# Copyright 2014 Jake Ross
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
from pychron.core.ui import set_qt

set_qt()

#============= enthought library imports =======================
from traits.api import HasTraits, Bool, Instance, Directory
from traitsui.api import View, Item, VGroup, HGroup, Controller
import apptools.sweet_pickle as pickle
#============= standard library imports ========================
import os
#============= local library imports  ==========================
from pychron.paths import paths


class TableSelectionModel(HasTraits):
    use_pdf_summary = Bool
    use_xls_summary = Bool

    use_pdf_data = Bool
    use_xls_data = Bool
    root = Directory
    auto_view = Bool


class TableSelectionDialog(Controller):
    model = Instance(TableSelectionModel)

    def __init__(self, *args, **kw):
        super(TableSelectionDialog, self).__init__(*args, **kw)

        p = os.path.join(paths.hidden_dir, 'table_selection_dialog')
        if os.path.isfile(p):
            with open(p, 'r') as fp:
                try:
                    self.model = pickle.load(fp)
                except (pickle.PickleError, OSError, EOFError):
                    pass

    def closed(self, info, is_ok):
        if is_ok:
            p = os.path.join(paths.hidden_dir, 'table_selection_dialog')
            with open(p, 'w') as fp:
                try:
                    pickle.dump(self.model, fp)
                except pickle.PickleError:
                    pass

    def traits_view(self):
        sum_grp = VGroup(Item('use_pdf_summary', label='PDF'),
                         Item('use_xls_summary', label='Excel'),
                         show_border=True,
                         label='Summary')
        data_grp = VGroup(Item('use_pdf_data', label='PDF'),
                          Item('use_xls_data', label='Excel'),
                          show_border=True,
                          label='Data Table')
        v = View(VGroup(Item('root', label='Save Dir.'),
                        HGroup(sum_grp, data_grp,
                               Item('auto_view',
                                    tooltip='Automatically view constructed tables in an external editor '
                                            'when finished',
                                    label='Auto View Tables'))),
                 resizable=True,
                 title='Table Selection',
                 buttons=['OK', 'Cancel'],
                 width=400)
        return v


if __name__ == '__main__':
    t = TableSelectionDialog()
    t.configure_traits()

#============= EOF =============================================

