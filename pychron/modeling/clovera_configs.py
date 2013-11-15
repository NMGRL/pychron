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
from traits.api import  Str, Int, Float, Bool, Array, Property
from traitsui.api import View, Item, ModalButtons, Handler, \
     EnumEditor, HGroup, Label, Spring
#============= standard library imports ========================
import os
from numpy import ones, save, load
#============= local library imports  ==========================
from pychron.loggable import Loggable
class BaseConfigHandler(Handler):
    def closed(self, info, is_ok):
        if is_ok:
            info.object.dump()

class BaseConfig(Loggable):
    root = None
    runid = Str
    _dump_attrs = None
    def __init__(self, rid, root, *args, **kw):
        super(BaseConfig, self).__init__(*args, **kw)
        self.runid = rid
        self.root = root

    def dump(self):
        if self._dump_attrs is None:
            raise NotImplementedError('set _dump_attrs')

        p = self.get_path()
        self.info('saving configuration to {}'.format(p))
        self._dump_hook(p)

    def _dump_hook(self, p):
        with open(p, 'w') as f:
            prep = lambda x: (1 if x else 0) if isinstance(x, bool) else x
            txt = '\n'.join([str(prep(getattr(self, attr))) for attr in self._dump_attrs])
            f.write(txt)

    def get_directory(self):
        return os.path.join(self.root, self.runid)

    def get_path(self):
        p = os.path.join(self.get_directory(), '{}.cl'.format(self.klass_name))
        return p

    def _get_buttons(self):
        return ModalButtons[1:]

class AutoUpdateParseConfig(BaseConfig):
    tempoffset = Float(90)
    timeoffset = Float(2)


    def traits_view(self):
        v = View('tempoffset',
               'timeoffset',
               buttons=self._get_buttons(),
               kind='livemodal',
               title='Autoupdate Parse Configuration'
               )
        return v

class FilesConfig(BaseConfig):
    klass_name = 'files'
    #===========================================================================
    # config params
    #===========================================================================

    STOP = 'stop'
    n = 'n'
    _dump_attrs = ['n', 'runid', 'STOP']

class AutoarrConfig(BaseConfig):
    klass_name = 'autoarr'
    #===========================================================================
    # config params
    #===========================================================================
    automate_arrhenius_parameters = Bool(False)
    max_domains = Int
    min_domains = Int
    fixed_Do = Bool
    activation_energy = Float
    ordinate_Do = Float
    max_domain_size = Float
    _dump_attrs = ['automate_arrhenius_parameters',
               'max_domains',
               'min_domains',
               'fixed_Do',
               'activation_energy',
               'ordinate_Do',
               'max_domain_size'
               ]

    def traits_view(self):
        v = View(Item('automate_arrhenius_parameters'),
               Item('max_domains'),
               Item('min_domains'),
               Item('fixed_Do', label='Fixed Do.'),
               Item('activation_energy'),
               Item('ordinate_Do', label='Ordinate Do.'),
               Item('max_domain_size', label='Max. Domain Size'),
               buttons=self._get_buttons(),
               handler=BaseConfigHandler,
               title='Autoarr Configuration',
               kind='livemodal'

               )

        return v


# def validate_nruns(obj, name, value):
#    try:
#        m = float(value)
#        if m <= 20 or m >= 199:
#            return value
#    except:
#        return value


class AutoagemonConfig(BaseConfig):
    klass_name = 'autoagemon'
    #===========================================================================
    # config params
    #===========================================================================
    nruns = Property()
    _nruns = Int(21)
    max_plateau_age = Float(1000)
    _dump_attrs = ['nruns', 'max_plateau_age']

    def _validate_nruns(self, value):
        try:
            m = int(value)
            if m >= 20 or m <= 199:
                return m
        except:
            return

    def _get_nruns(self):
        return self._nruns

    def _set_nruns(self, v):
        if v is not None:
            self._nruns = v

    def traits_view(self):
        v = View(Item('nruns', label='NRuns (min=21, max=199)'),
                 Item('max_plateau_age', label='Max. Plateau Age (Ma)'),
                 buttons=self._get_buttons(),
                 handler=BaseConfigHandler,
                 title='Autoagemon Configuration',
                 kind='livemodal'
               )
        return v

class AutoagefreeConfig(BaseConfig):
    klass_name = 'autoagefree'
    #===========================================================================
    # config params
    #===========================================================================
    nruns = Int(200)
    max_plateau_age = Float
    use_contour = Bool(True)
    min_age = Float
    _dump_attrs = ['nruns', 'max_plateau_age',
                   'use_contour', 'min_age'
                   ]
    def traits_view(self):
        v = View(Item('nruns', label='Number of runs'),
                 Item('max_plateau_age', label='Max. Plateau Age (Ma)'),
                 Item('use_contour', label='Create Contours'),
                 Item('min_age', enabled_when='object.use_contour',
                      label='Minimum contour age (Ma)'),
                 buttons=self._get_buttons(),
                 handler=BaseConfigHandler,
                 title='Autoagefree Configuration',
                 kind='livemodal'
               )
        return v

class CorrelationConfig(BaseConfig):
    klass_name = 'corrfft'
    #===========================================================================
    # config params
    #===========================================================================
    f_min = Float
    f_max = Float


    _dump_attrs = ['_f_min', '_f_max']

    def _get_fmin(self):
        return self.f_min / 100.
    def _get_fmax(self):
        return self.f_max / 100.

    _f_min = property(fget=_get_fmin)
    _f_max = property(fget=_get_fmax)

    def traits_view(self):
        v = View(Item('f_min', label='F minimum (%)'),
                 Item('f_max', label='F maximum (%)'),
                 buttons=self._get_buttons(),
                 handler=BaseConfigHandler,
                 title='Correlation Configuration',
                 kind='livemodal'
               )
        return v
class ArrmeConfig(BaseConfig):
    klass_name = 'arrme'

    geometry = Int(2)
    _dump_attrs = ['geometry']
    def traits_view(self):
        v = View(
                 Item('geometry', editor=EnumEditor(values={1:'1:Slabs',
                                                            2:'2:Spheres',
                                                            3:'3:Cylinders'})),
                 buttons=self._get_buttons(),
                 handler=BaseConfigHandler,
                 title='Arrme Configuration',
                 kind='livemodal'
               )
        return v

class AgesmeConfig(BaseConfig):
    klass_name = 'agesme'
    cooling_history = Array(int, (20, 2))
    geometry = Int(2)

    _dump_attrs = []
    def __init__(self, *args, **kw):
        super(AgesmeConfig, self).__init__(*args, **kw)

        p = os.path.join(self.get_directory(), 'cooling_history.npy')
        if os.path.isfile(p):
            self.cooling_history = load(p)
        else:
            self.cooling_history = ones((20, 2)) * -1

#        #load a default or previous cooling history
#        for i in range(10):
#            self.cooling_history[i] = [300 - i * 10, 4]

    def _dump_hook(self, p):
        new_line = chr(10)
        line_str = '{}' + new_line

        with open(p, 'w') as f:
            # write 1 indicating thermal history correct is correct
            f.write(line_str.format('1'))
            f.write(str(self.geometry))

        ap = os.path.join(os.path.dirname(p), 'agesme.in')
        with open(ap, 'w') as f:
            # write the cooling history
            ch = ['\t'.join(map(str, r)) for r in self.cooling_history if r[0] >= 0 and r[1] >= 0]
            f.write(line_str.format(len(ch)))
            f.write(new_line.join(ch))

            f.write(new_line)

            # write contents of arr-me.in
            pp = os.path.join(os.path.dirname(p), 'arr-me.in')
            with open(pp, 'r') as ff:
                f.write(ff.read())


            chp = os.path.join(os.path.dirname(p), 'cooling_history.npy')
            save(chp, self.cooling_history)

    def traits_view(self):
        v = View(
                 HGroup(Label('Age (Ma)'), Spring(width=55, springy=False), Label('Temp (C)')),
                 Item('cooling_history', show_label=False),
                 Item('geometry', show_label=False,
                      editor=EnumEditor(values={1:'1:Slabs',
                                                2:'2:Spheres',
                                                3:'3:Cylinders'})),

                 buttons=self._get_buttons(),
                 handler=BaseConfigHandler,
                 title='Agesme Configuration',
                 kind='livemodal'
               )
        return v


# class ConfidenceIntervalConfig(BaseConfig):
#    klass_name = 'confint'
#    #===========================================================================
#    # config params
#    #===========================================================================
#    max_age = Float(500)
#    min_age = Float(0)
#    nsteps = Int(100)
#
#    _dump_attrs = ['max_age', 'min_age', 'nsteps']
#    def traits_view(self):
#        v = View(Item('max_age', label='Max. age (Ma)'),
#                 Item('min_age', label='Min. age (Ma)'),
#                 Item('nsteps'),
#                 buttons=self._get_buttons(),
#                 handler=BaseConfigHandler,
#                 title='Confidence Interval Configuration',
#                 kind='livemodal'
#               )
#        return v


if __name__ == '__main__':
    from pychron.helpers.logger_setup import logging_setup
    logging_setup('fop')
    a = AgesmeConfig('Desktop', '/Users/ross')
    a.configure_traits()

#    a = ConfidenceIntervalConfig('12345-01', '/Users/Ross/Desktop')
#    info = a.configure_traits()
#    if info:
#        print 'foo'

#============= EOF =====================================

