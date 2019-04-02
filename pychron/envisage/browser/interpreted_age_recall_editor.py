# ===============================================================================
# Copyright 2018 ross
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
from traits.api import HasTraits, Either, Float, Str, Int, List, Property
from traitsui.api import View, UItem, TabularEditor
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.helpers.formatting import floatfmt
from pychron.envisage.browser.recall_editor import BaseRecallEditor
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA, PLUSMINUS_PERCENT, NULL_STR


class IAValuesAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Value', 'value')]


class IAUValuesAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Value', 'value'),
               ('Kind', 'kind'),
               (PLUSMINUS_ONE_SIGMA, 'error'),
               (PLUSMINUS_PERCENT, 'percent_error')]

    value_text = Property
    error_text = Property
    percent_error_text = Property

    def _get_value_text(self):
        return floatfmt(self.item.value)

    def _get_error_text(self):
        return floatfmt(self.item.error)

    def _get_percent_error_text(self):
        ret = self.item.percent_error
        if ret != NULL_STR:
            ret = floatfmt(self.item.percent_error, 2)
        return ret


class IAAnalysesAdapter(TabularAdapter):
    columns = [('RunID', 'record_id'),
               ('Age', 'age'),
               (PLUSMINUS_ONE_SIGMA, 'age_err'),
               ('{} w/o J'.format(PLUSMINUS_ONE_SIGMA), 'age_err_wo_j'),
               ('40Ar*', 'radiogenic_yield'),
               (PLUSMINUS_ONE_SIGMA, 'radiogenic_yield_err'),
               ('K/Ca', 'kca'),
               (PLUSMINUS_ONE_SIGMA, 'kca_err'),
               ('K/Cl', 'kcl'),
               (PLUSMINUS_ONE_SIGMA, 'kcl_err')]


class IAValue(HasTraits):
    name = Str
    value = Either(Int, Float, Str)

    def __init__(self, name, value):
        self.name = name
        self.value = value
        super(IAValue, self).__init__()


class IAUValue(IAValue):
    error = Float
    kind = Str

    def __init__(self, name, value, error=None, kind=None):
        super(IAUValue, self).__init__(name, value)
        if error is not None:
            self.error = error
        if kind is not None:
            self.kind = kind

    @property
    def percent_error(self):
        if isinstance(self.value, float):
            try:
                return self.error / self.value * 100
            except ZeroDivisionError:
                return NULL_STR


class IAAnalysis(HasTraits):
    record_id = Str

    age = Float
    age_err = Float
    age_err_wo_j = Float
    radiogenic_yield = Float
    radiogenic_yield_err = Float
    kca = Float
    kca_err = Float
    kcl = Float
    kcl_err = Float

    def __init__(self, d):
        for attr in ('record_id', 'age', 'age_err', 'age_err_wo_j',
                     'kca', 'kca_err', 'kcl', 'kcl_err'):
            try:
                v = d[attr]
                setattr(self, attr, v)
            except KeyError:
                pass


class InterpretedAgeRecallEditor(BaseRecallEditor):
    values = List
    uvalues = List

    def __init__(self, item, *args, **kw):
        super(InterpretedAgeRecallEditor, self).__init__(*args, **kw)
        self.basename = item.name

        attrs = ('sample', 'lithology', 'identifier', 'material', 'irradiation', 'project')

        vs = [IAValue(s, getattr(item, s)) for s in attrs]

        vs.append(IAValue('N', int(getattr(item, 'nanalyses'))))
        self.values = vs

        attrs = ('age', 'kca')
        self.uvalues = [IAUValue(s, getattr(item, s),
                                 getattr(item, '{}_err'.format(s)),
                                 getattr(item, '{}_kind'.format(s))) for s in attrs]
        self.analyses = [IAAnalysis(d) for d in item.analyses]

    def traits_view(self):
        v = View(UItem('values', editor=TabularEditor(adapter=IAValuesAdapter())),
                 UItem('uvalues', editor=TabularEditor(adapter=IAUValuesAdapter())),
                 UItem('analyses', editor=TabularEditor(adapter=IAAnalysesAdapter())))
        return v
# ============= EOF =============================================
