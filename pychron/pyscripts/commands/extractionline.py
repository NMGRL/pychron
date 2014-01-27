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
from traits.api import Str, Float
from traitsui.api import Item
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.pyscripts.commands.core import Command
from pychron.pyscripts.commands.valve import ValveCommand


class Disable(Command):
    pass


class DrillPoint(Command):
    pass


class Enable(Command):
    pass


class MovingExtract(Command):
    pass


class Prepare(Command):
    pass


class SetMotor(Command):
    pass


class SetMotorLock(Command):
    pass


class Snapshot(Command):
    pass


class Autofocus(Command):
    pass


class StartVideoRecording(Command):
    pass


class StopVideoRecording(Command):
    pass


class VideoRecording(Command):
    pass


class TracePath(Command):
    pass


class Degas(Command):
    pass


class PowerMap(Command):
    pass


class Open(ValveCommand):
    description = 'Open a valve'
    example = '''1. open("V")
2. open(description="Bone to Turbo")
'''


class Close(ValveCommand):
    description = 'Close a valve'
    example = '''1. open("V")
2. close(description="Bone to Turbo")
'''


class IsOpen(ValveCommand):
    description = 'Check if a valve is Open'
    example = '''1. is_open("V")
2. is_open(description="Bone to Turbo")
'''


class IsClosed(ValveCommand):
    description = 'Check if a valve is Closed'
    example = '''1. is_closed("V")
2. is_closed(description="Bone to Turbo")
'''


class NameCommand(Command):
    name = Str

    def _get_view(self):
        return Item('name', width=300)

    def _to_string(self):
        return self._keyword('name', self.name)


class Release(NameCommand):
    description = ''
    example = ''


class Acquire(NameCommand):
    description = 'Acquire a resource'
    example = '''acquire('foo')'''


class MoveToPosition(Command):
    position = Str

    def _get_view(self):
        return Item('position')

    def _to_string(self):
        return '{}'.format(self.position)


class ExecutePattern(Command):
    description = 'Execute a pattern'
    example = 'execute_pattern("diamond")'


class ValueCommand(Command):
    value = Float

    def _get_view(self):
        return Item('value')

    def _to_string(self):
        return '{}'.format(self.value)


class Extract(ValueCommand):
    description = 'Set extraction device to specified value'
    example = ''


class EndExtract(Command):
    description = ''
    example = ''


class SetTray(Command):
    description = ''
    example = ''


class SetResource(Command):
    description = ''
    example = ''


class GetResourceValue(Command):
    description = ''
    example = ''


class SetPositionCommand(ValueCommand):
    pass


class SetX(SetPositionCommand):
    pass


class SetY(SetPositionCommand):
    pass


class SetZ(SetPositionCommand):
    pass


class SetXy(Command):
    xvalue = Float
    yvalue = Float

    def _get_view(self):
        return Item('xvalue', 'yvalue')

    def _to_string(self):
        return '{},{}'.format(self.xvalue, self.yvalue)

class GetValue(Command):
    pass

# class HeatSample(Command):
#    value = Float
#    def _get_view(self):
#        return Item('value')
#
#    def _to_string(self):
#        return '{}'.format(self.value)

#============= EOF =============================================
