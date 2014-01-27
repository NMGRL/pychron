#===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Int, Str, Bool, List, Event, Property, Enum, Float
from traitsui.api import Item, CheckListEditor, VGroup, HGroup, ButtonEditor, EnumEditor
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.pyscripts.commands.core import Command

from pychron.paths import paths
import os
from pychron.pyscripts.commands.valve import ValveCommand
from pychron.pychron_constants import NULL_STR

DETS = ['H2', 'H1', 'AX', 'L1', 'L2', 'CDD']

#===============================================================================
# super commands
#===============================================================================
class ValueCommand(Command):
    value = Float

    def _get_view(self):
        v = VGroup('value')
        return v

    def _to_string(self):
        return self.value


class ConditionCommand(Command):
    attribute = Str
    comparison = Enum('<', '>', '=', '<=', '>=')
    value = Float
    start_count = Int(0)
    frequency = Int(10)

    def _get_condition_group(self):
        g = HGroup('attribute',
                   'comparison',
                   'value'
        )
        o = HGroup('start_count', 'frequency')
        return VGroup(g, o)

    def _to_string(self):
        return '"{}","{}","{}", start_count={}, frequency={}'.format(self.attribute,
                                                                     self.comparison,
                                                                     self.value,
                                                                     self.start_count,
                                                                     self.frequency)

        #===============================================================================

# condition commands
#===============================================================================
class AddTermination(ConditionCommand):
    description = 'Add termination condition'
    example = ''' '''

    def _get_view(self):
        return self._get_condition_group()


class AddAction(ConditionCommand):
    action = Str
    resume = Bool(False)
    description = 'Add action condition'
    example = ''' '''

    def _get_view(self):
        g = self._get_condition_group()
        return VGroup(g, 'action', 'resume')

    def _to_string(self):
        s = super(AddAction, self)._to_string()
        return '{}, action="{}", resume={}'.format(s, self.action, self.resume)


class AddTruncation(ConditionCommand):
    description = 'Add truncation condition'
    example = ''' '''


class ClearConditions(Command):
    description = 'Clear all conditions'
    example = ''' '''


class ClearActions(Command):
    description = 'Clear actions'
    example = ''' '''


class ClearTruncations(Command):
    description = 'Clear truncations'
    example = ''' '''


class ClearTerminations(Command):
    description = 'Clear terminations'
    example = ''' '''

#===============================================================================
#
#===============================================================================

class Equilibrate(ValveCommand):
    description = 'Equilibrate'
    example = ''' '''
    eqtime = Float(20)
    inlet = Str
    outlet = Str
    do_post_equilibration = Bool

    def _get_valve_names(self):
        vs = super(Equilibrate, self)._get_valve_names()
        return [(NULL_STR, NULL_STR)] + vs

    def _get_view(self):
        v = VGroup(Item('eqtime', label='Equilibration Time (s)'),
                   Item('inlet', editor=EnumEditor(name='valve_name_dict')),
                   Item('outlet', editor=EnumEditor(name='valve_name_dict')),
                   'do_post_equilibration'
        )

        return v

    def _to_string(self):
        words = [('eqtime', self.eqtime, True)]

        if self.inlet and self.inlet != NULL_STR:
            words.append(('inlet', self.inlet))

        if self.outlet and self.outlet != NULL_STR:
            words.append(('outlet', self.outlet))

        if self.do_post_equilibration is not None:
            words.append(('do_post_equilibration',
                          self.do_post_equilibration, True))

        return self._keywords(words)


class ExtractionGosub(Command):
    description = 'Execute an extraction gosub'
    example = ''' '''
    gosub = Str
    names = Property

    def _get_names(self):
        p = os.path.join(paths.extraction_dir)
        names = [pi for pi in os.listdir(p) if pi.endswith('.py')]
        return names

    def _get_view(self):
        v = VGroup(Item('gosub', editor=EnumEditor(name='names')))
        return v

    def _to_string(self):
        return self.gosub


class GetIntensity(Command):
    description = 'Get detector intensity'
    example = ''' '''
    detector = Str(DETS[0])

    def _get_view(self):
        return VGroup(Item('detector', editor=EnumEditor(values=DETS)))

    def _to_string(self):
        return self._quote(self.detector)


class Baselines(Command):
    ncounts = Int(1)
    position = Float
    detector = Str('H1')

    description = 'Measure baselines'
    example = '''1. baselines(counts=50, mass=40.5)
2. baselines(counts=5, cycles=5, mass=0.5, detector='CDD')

Example 1. multicollects baselines at mass 40.5 for 50 counts. 
    Only activated detectors are records (see. activate_detectors)

Example 2. peak hops activated isotopes on the CDD. In this case <mass> is relative.
    <counts> is the number of integrates per cycle
    <cycles> is the total number of peak jumps 
'''

    def _get_view(self):
        return VGroup(Item('ncounts'),
                      Item('position'),
                      Item('detector', editor=EnumEditor(values=DETS))
        )

    def _to_string(self):
        pos = self.position
        if not pos:
            pos = None

        words = [('ncounts', self.ncounts, True),
                 ('position', pos, True),
                 ('detector', self.detector)
        ]

        return self._keywords(words)


class PositionMagnet(Command):
    description = 'Alter magnetic field to position beams'
    example = '''1. position(39.962)
2. position('Ar40', detector="H1")
3. position(5.89813, dac=True)

Example 1. moves the mass 39.962 to AX detector

Example 2. moves 'Ar40' to H1 detector. 
          'Ar40' is converted to a mass using the MolecularWeightsTable
          
Example 3. positions the magnet in DAC space. 
         
         !!Remember to set dac=True otherwise the position will be 
           interpreted as a mass
    
'''

    def _get_view(self):
        pass

    def _to_string(self):
        pass


class SetTimeZero(Command):
    description = 'Set Time Zero'
    example = u'''set_time_zero()
    
set_time_zero allows fine grained control of the t\u2080.    
'''

    def _get_view(self):
        pass

    def to_string(self):
        return 'set_time_zero()'


class PeakCenter(Command):
    description = 'Scan the magnet to locate the center of a peak'
    example = '''1. peak_center()
2. peak_center(detector='H1', isotope='Ar39')

Example 1. Scan Ar40 over the AX detector

Example 2. Scan Ar39 over the H1 detector
'''

    def _get_view(self):
        pass

    def _to_string(self):
        pass


class ActivateDetectors(Command):
    detectors = List
    toggle = Event
    toggle_label = Property(depends_on='_toggled')
    _toggled = Bool(False)

    description = 'Define list of detector to record'
    example = '''activate_detectors('H1','AX','CDD')
'''

    def _toggle_fired(self):
        if not self._toggled:
            self.detectors = DETS
        else:
            self.detectors = []
        self._toggled = not self._toggled

    def _get_toggle_label(self):
        return 'None' if self._toggled else 'All'

    def _get_view(self):
        return VGroup(Item('detectors',
                           show_label=False,
                           style='custom',
                           editor=CheckListEditor(values=DETS,
                                                  cols=1
                           )),
                      Item('toggle',
                           show_label=False,
                           editor=ButtonEditor(label_value='toggle_label'))
        )

    def _to_string(self):
        return ', '.join([self._quote(di) for di in self.detectors])


class Multicollect(Command):
    ncounts = Int(1)
    integration_time = Float

    description = 'Simultaneously record data from all activated detectors'
    example = '''1. multicollect(ncounts=200)
2. multicollect(ncounts=200, integration_time=2.097152)

!!setting the integration_time is currently not available because of a bug in Qtegra/RCS!!
    .
'''

    def _get_view(self):
        return VGroup(Item('ncounts'), Item('integration_time'))

    def _to_string(self):
        words = [('ncounts', self.ncounts, True),
                 ('integration_time', self.integration_time, True)
        ]
        return self._keywords(words)


class Regress(Command):
    kind = Enum('linear', 'parabolic', 'cubic')

    description = 'Set the default peak-time regression fits'
    example = '''1. regress('parabolic')
2. activate_detectors('AX','CDD')
   regress('parabolic','linear')
   
Example 1. set all activated detectors to use a 'parabolic' fit
Example 2. set AX to parabolic and CDD to linear

!!call 'regress' only after detectors have been activated!!
    
'''

    def _get_view(self):
        return Item('kind', show_label=False)

    def _to_string(self):
        return self._keyword('kind', self.kind)


class Sniff(Command):
    ncounts = Int(1)

    description = '''Record activated detectors, but do not use in peak-time regression. 
Useful for measuring signals during equilibration'''

    example = '''sniff(ncounts=20)'''

    def _get_view(self):
        return Item('ncounts')

    def _to_string(self):
        return self._keyword('ncounts', self.ncounts, True)


class PeakHop(Command):
    description = 'Peak hop a mass on a detector'
    example = '''1. peak_hop(detector='CDD', isotopes=['Ar40','Ar39'])
2. peak_hop(detector='CDD', isotopes=['Ar40','Ar39'], cycles=10, integrations=10)
    
    peak hops isotopes Ar40, Ar39 on the CDD.
    <counts> is the number of integrates per cycle --default=5
    <cycles> is the total number of peak jumps --default=5'''

    def _get_view(self):
        pass

    def _to_string(self):
        pass


class Coincidence(Command):
    description = '''A coincidence scan is similar to a peak_center 
however all peak centers for all activated detectors are determined'''
    example = 'coincidence()'

    def _get_view(self):
        pass

    def _to_string(self):
        pass


#===============================================================================
# set commands
#===============================================================================
class SetDeflection(ValueCommand):
    description = 'Set deflection of a detector'
    example = 'set_deflection("AX", 100)'
    detector = Str(DETS[0])

    def _get_view(self):
        v = VGroup(Item('detector', editor=EnumEditor(values=DETS)),
                   'value'
        )
        return v

    def _to_string(self):
        return '"{}", {}'.format(self.detector, self.value)


class SetNcounts(Command):
    description = 'Set number of counts'
    example = ''' '''
    counts = Int

    def _get_view(self):
        v = VGroup('counts')
        return v

    def _to_string(self):
        return self.counts


class SetDeflections(Command):
    description = 'Set detector deflections'
    example = ''' '''


class SetSourceOptics(Command):
    description = 'Set Source Optics'
    example = ''' '''


class SetSourceParameters(Command):
    description = 'Set source parameters'
    example = ''' '''


class SetCddOperatingVoltage(ValueCommand):
    description = 'Set CDD operating voltage'
    example = ''' '''


class SetYsymmetry(ValueCommand):
    description = 'Set y-symmetry'
    example = 'set_y_symmetry(10.1)'


class SetZsymmetry(ValueCommand):
    description = 'Set z-symmetry'
    example = 'set_z_symmetry(10.1)'


class SetZfocus(ValueCommand):
    description = 'Set z-focus'
    example = 'set_z_focus(10.1)'


class SetExtractionLens(ValueCommand):
    description = 'Set extraction lens'
    example = 'set_extraction_lens(10.1)'


class DefineDetectors(Command):
    pass


class DefineHops(Command):
    pass


class GetDeflection(Command):
    pass


class IsLastRun(Command):
    pass


class LoadHops(Command):
    pass


class SetBaselineFits(Command):
    pass


class SetFits(Command):
    pass


class SetIntegrationTime(Command):
    pass


#============= EOF =============================================
