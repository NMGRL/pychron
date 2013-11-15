#===============================================================================
# Copyright 2011 Jake Ross
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




#=============enthought library imports=======================
from traits.api import HasTraits, Any, Int, List, Enum, String, Float, Str
from traitsui.api import View, Item, VGroup, TableEditor
from traitsui.list_str_adapter import ListStrAdapter

from traitsui.table_column import ObjectColumn
#=============standard library imports ========================

import re
#=============local library imports  ==========================

func_regex = re.compile(r'p\[[0-9]\]')


class Adapter(ListStrAdapter):

    def get_bg_color(self, obj, trait, index):
        if index in [3]:
            return 'black'

    def get_text_color(self, obj, trait, index):
        if index in [3]:
            return 'yellow'


class StatsTableItem(HasTraits):
    name = Str
    value = Str


class CustomEquation(HasTraits):
    example = 'p[0]+p[1]*cos(p[2]*x)'
    equation = String('p[0]+x**2+p[1]*cos(2*x)+p[2]*sin(2*x)')
    initial_guess = String('1,1,1')
    v = View(Item('example', style='readonly'),
           Item('equation', label='Y ='),
           Item('initial_guess'),
           resizable=True,
           kind='modal',
           buttons=['OK', 'Cancel']
           )


class RegressionEditor(HasTraits):
    '''
    '''
    fit_type = Enum('linear', 'parabolic', 'average +/- SD', 'average +/- SEM', 'cubic', 'exponential', 'custom')
    id = Int
    graph = Any
    stats = List
    fitfunc = ''

    intercept = Float(editable=False)
    intercept_error = Float

    def __init__(self, *args, **kw):
        '''
        '''
        super(RegressionEditor, self).__init__(*args, **kw)
        self.on_trait_change(self.graph._metadata_changed, 'fit_type')

    def _fit_type_changed(self):
        '''
        '''
        if self.fit_type == 'custom':

            c = CustomEquation()
            info = c.edit_traits()
            if info.result:
                self.graph.fitfunc = c.equation

                alpha = 'abcdefg'
                ff = c.equation
                for a, ci in zip(alpha, func_regex.findall(c.equation)):
                    ff = ff.replace(ci, a)

                self.fitfunc = ff
                self.graph.initial_guess = [float(ci) for ci in c.initial_guess.split(',')]

            else:
                return

        self.graph.fit_types[self.id] = self.fit_type
        self.graph.selected_plotid = self.id

    def set_regression_statistics(self, rdict, plotid=0):
        '''

        '''
        coeffs = rdict['coefficients']
        coeff_errs = rdict['coeff_errors']

        # stats = rdict['statistics']

        exp_fmt = '%0.8G'
        alpha = 'abcd'
        if coeffs is None:
            return

        if len(coeffs) == 1:
            strfunc = self.fit_type
            strcoeffs = exp_fmt % coeffs[0]
            strcoeff_errs = '%s (%0.3f%%)' % (exp_fmt % coeff_errs[0], float(coeff_errs[0]) / float(coeffs[0]) * 100)
            # intercept = 'Intercept %0.5e +/- %0.5e (%0.3f%%)' % (coeffs[0], coeff_errs[0], float(coeff_errs[0]) / float(coeffs[0]) * 100)

            strcoeffs_item = StatsTableItem(name='Average',
                                        value=strcoeffs)
            strcoeff_errs_item = StatsTableItem(name='Average Error',
                                                value=strcoeff_errs)

            intercept = exp_fmt % coeffs[0]
            intercept_err = exp_fmt % coeff_errs[0]
            intercept_err_percent = exp_fmt % (abs(coeff_errs[0] / coeffs[0]) * 100)

            # self.intercept = coeffs[0]
            # intercept =

        else:
            strcoeffs = '  '.join(['%s = %s, ' % (alpha[i], exp_fmt % arg) for i, arg in enumerate(coeffs)]).rstrip()[:-1]

            strcoeff_errs = '  '.join(['%s = %0.4G, (%0.3f%%), ' % (alpha[i], float(arg[1]),
                                                                 abs(float(arg[1]) / float(arg[0]) * 100) if arg[0] != 0 else 0) for i, arg in enumerate(zip(coeffs, coeff_errs))])
            strcoeff_errs = strcoeff_errs.rstrip()[:-1]

            if self.fit_type == 'custom':
                strfunc = self.fitfunc
            elif len(coeffs) == 2:
                strfunc = 'y = a*x+b'
            elif len(coeffs) == 3:
                strfunc = 'y = a*x^2+b*x+c'
            elif len(coeffs) == 4:
                strfunc = 'y = a*x^3+b*x^2+c*x+d'

            icoef = float(coeffs[-1])
            icoef_err = 0
            if len(coeff_errs) > 0:
                icoef_err = float(coeff_errs[-1])
            if self.fit_type == 'exponential':
                strfunc = 'a*exp(b*x)'
                icoef = float(coeffs[0])
                icoef_err = float(coeff_errs[0])

            # intercept = '%0.8G +/- %0.8G (%0.3f%%)' % (icoef, icoef_err, abs(icoef_err / icoef * 100))

            intercept = exp_fmt % icoef
            intercept_err = exp_fmt % icoef_err
            intercept_err_percent = '%0.3f' % (abs(icoef_err / icoef) if icoef != 0 else 0 * 100)

            strcoeffs_item = StatsTableItem(name='Coefficients',
                                        value=strcoeffs)
            strcoeff_errs_item = StatsTableItem(name='Coefficient Errors',
                                                value=strcoeff_errs)

#        stddev = 'standard deviation = %0.5G' % stats['stddev']
#        sample_stddev = 'sample standard deviation = %0.5G' % stats['sample_stddev']
#        stderr_mean = 'standard error of mean = %0.5G' % stats['stderr_mean']
#        rr = 'R squared = %0.5f' % stats['r_squared']

        stats = self.stats

        strfunc_item = StatsTableItem(name='Fit Function',
                                    value=strfunc)

        intercept_item = StatsTableItem(name='Y Intercept',
                                      value=intercept
                                      )

        intercept_err_item = StatsTableItem(name='Y Intercept Error',
                                            value=intercept_err)

        intercept_err_percent_item = StatsTableItem(name='Y Intercept Error (%)',
                                            value=intercept_err_percent)

        if stats:
#            stats[0] = strfunc
#            stats[1] = strcoeffs
#            stats[2] = strcoeff_errs
#
#            stats[3] = intercept
#
#            stats[4] = rr
#            stats[5] = stddev
#            stats[6] = sample_stddev
#            stats[7] = stderr_mean

            stats[0] = strfunc_item
            stats[1] = strcoeffs_item
            stats[2] = strcoeff_errs_item
            stats[3] = intercept_item
            stats[4] = intercept_err_item
            stats[5] = intercept_err_percent_item

        else:
            stats.append(strfunc_item)
            stats.append(strcoeffs_item)
            stats.append(strcoeff_errs_item)
            stats.append(intercept_item)
            stats.append(intercept_err_item)
            stats.append(intercept_err_percent_item)
#            stats.append(strfunc)
#            stats.append(strcoeffs)
#            stats.append(strcoeff_errs)
#            stats.append(intercept)
#            stats.append(rr)
#            stats.append(stddev)
#            stats.append(sample_stddev)
#            stats.append(stderr_mean)

    def traits_view(self):
        '''
        '''
        cols = [
                ObjectColumn(name='name', editable=False, width=125),
                ObjectColumn(name='value', width=0.80)
                ]
        editor = TableEditor(columns=cols,
                             show_column_labels=False,
                             auto_size=False,
                             selection_mode='cell'
                             )

        return View(VGroup(
                           Item('fit_type', show_label=False),
#                           HGroup(Item('intercept', format_str = '%0.8G', width = 0.5),
#                                  Item('intercept_error', format_str = '%0.8G', width = 0.5)),
                           Item('stats', editor=editor, show_label=False)
                           )
                    )
#========================= EOF =========================
# class RegressionGroupEditor(HasTraits):
#    '''
#        G{classtree}
#    '''
#  #  update_flag = Bool
#
#    graph = Any
#
#
#    regression_editors = List()
#
# #    def __init__(self, *args, **kw):
# #        '''
# #        '''
# #        super(RegressionGroupEditor, self).__init__(*args, **kw)
#
#  #      self._build_()
#
# #        self.on_trait_change(self.graph._metadata_changed,
# #                             'update_flag')
# #
#
#
# #    def _anytrait_changed(self, name, old, new):
# #        '''
# #            @_type name: C{str}
# #            @param name:
# #
# #            @_type old: C{str}
# #            @param old:
# #
# #            @_type new: C{str}
# #            @param new:
# #        '''
# #        if '_type' in name:
# #            plotid = int(name[-1:])
# #
# #            self.graph.fit_types[plotid] = new
# #            self.graph.selected_plotid = plotid
# #
# #            self.update_flag = not self.update_flag
#
# #    def _build_(self):
# #        '''
# #        '''
# #        self.regression_editors=[]
# #        n = self.graph.get_num_plots()
# #        for i in range(n):
# #            #self.add_trait('_type%i' % i, 'linear')
# #            self.regression_editors.append(RegressionEditor(id=i,graph=self.graph))
# #
#    def add_editor(self):
#        ed = self.regression_editors
#        id = len(ed)
#        ed.append(RegressionEditor(id = id, graph = self.graph))
#
#    def traits_view(self):
#        v = View(Item('regression_editors',
#                    style = 'custom',
#                    show_label = False,
#                    editor = ListEditor(use_notebook = True,
#                                      dock_style = 'tab')))
#        return v
#
#    def set_regression_statistics(self, args, plotid = 0):
#
#        rstats = self.regression_editors[plotid]
#
#        alpha = 'abcd'
#        if len(args) == 1:
#            stats = 'average = %0.3f' % args[0]
#        else:
#            stats = '  '.join(['%s = %0.3f, ' % (alpha[i], arg) for i, arg in enumerate(args)])[:-2]
#
#        if rstats.stats:
#            rstats.stats[0] = stats
#        else:
#            rstats.stats.append(stats)
# #
# #    def _regression_statistics_group(self):
# #        return VGroup(Item('regression_stats',style='custom'))
#
# #    def traits_view(self):
# #        '''
# #        '''
# #        content = []
# #
# #        n = self.graph.get_num_plots()
# #        if n == 1:
# #            g = Group(Item('type0', editor = EnumEditor(values = self.type),
# #                         show_label = False))
# #            content.append(g)
# #        else:
# #            for i in range(n):
# #                id = (n - i - 1)
# #                g = Group(Item('type%i' % id, editor = EnumEditor(values = self.type),
# #                             show_label = False),
# #                        label = 'Fit %i' % id)
# #                content.append(g)
# #
# #        return View(Group(content = content))
