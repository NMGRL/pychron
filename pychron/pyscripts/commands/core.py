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
from traits.api import HasTraits, Str, Float, File, Property, Interface, implements
from traitsui.api import View, Item, FileEditor, VGroup, Group
from traitsui.menu import OKCancelButtons
#============= standard library imports ========================
import os
import re
#============= local library imports  ==========================
from pychron.paths import paths
first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')
def uncamelcase(name):
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()

readonly = lambda x, **kw: Item(x, style='readonly', show_label=False,
                                 **kw)


# class ICommand(Interface):
#    def to_string(self):
#        pass
#    def get_text(self):
#        pass

class Command(HasTraits):
    description = Str
    example = Str
    name = Property
#    implements(ICommand)

    def _get_name(self):
        return self._get_command()

    def to_string(self):
        m = '{}({})'.format(
                          self._get_command(),
                          self._to_string()
                          )
        return m
#        return self.indent(m)

    def _get_command(self):
        return uncamelcase(self.__class__.__name__)
#        return self.__class__.__name__.lower()

    def _to_string(self):
        return ''

    @classmethod
    def _keywords(cls, words):
        return ', '.join([cls._keyword(*args) for args in words])

    @classmethod
    def _keyword(cls, k, v, number=False):
        if not number:
            v = cls._quote(v)
        return '{}={}'.format(k, v)

    @classmethod
    def _quote(cls, m):
        return '"{}"'.format(m)

    @classmethod
    def indent(cls, m, n=1):
        ts = '    ' * n
        return '{}{}'.format(ts, m)


    def get_text(self):
        ok = True
        if hasattr(self, '_get_view'):
#            pass
            info = self.edit_traits(kind='modal')
#            ok = info.result

#        if ok:
        return self.to_string()

    def traits_view(self):
        v = View(self._get_view(),
                 title=self.__class__.__name__,
                 buttons=OKCancelButtons
                 )
        return v

    def help_view(self):
        v = View(self._get_help_view())
        return v

    def _get_view(self):
        return Item()
#        raise NotImplementedError

    def _get_help_view(self):
        return VGroup(
                      Group(
                            readonly('description'),
                            show_border=True,
                            label='Description',
                            ),
                      Group(
                            readonly('example',
                                     height=100
                                     ),
                            show_border=True,
                            label='Example',
                            ),
                      )

class Wait(Command):
    def get_text(self):
        return self.to_string()

    def _to_string(self):
        return 'evt'


class Info(Command):
    message = Str

    description = 'Display a message'
    example = "info('This is a message')"
    def _get_view(self):
        return Item('message', width=500)

    def _to_string(self):
        return self._keyword('message', self.message)

class Sleep(Command):
    duration = Float

    description = 'Pause execution for N seconds'
    example = 'sleep(5)'

    def _get_view(self):
        return Item('duration', label='Duration (s)')

    def _to_string(self):
        return self._keyword('duration', self.duration,
                             number=True)


class Gosub(Command):
    path = File

    description = 'Switch to another script'
    example = '''1. gosub("gosubname")
2. gosub(name='name', root=<path to folder>)
    
If <root> is omitted the path to the script is determined by the script type. e.i
MeasurementPyScripts live in ../scripts/measurement

'''
    def _get_view(self):
        return Item(
                    'path',
                    style='custom',
                    show_label=False,
                    editor=FileEditor(
                                      filter=['*.py'],
                                      root_path=paths.scripts_dir,
                                      ),
#                    width=600,
                    )

    def _to_string(self):
        print self.path
        if os.path.isfile(self.path):
            head, tail = os.path.split(self.path)
            words = [('name', tail),
                     ('root', head),
                     ]
            return self._keywords(words)

class BeginInterval(Command):
    duration = Float
    def _get_view(self):
        return Item('duration', label='Duration (s)')

    def to_string(self):
        m = 'begin_interval(duration={})'.format(self.duration)
        m2 = 'complete_interval()'
        return self.indent(m) + '\n    \n' + self.indent(m2)


class CompleteInterval(Command):
    def get_text(self):
        return self.indent('complete_interval()')

class Interval(Command):
    pass

class Exit(Command):
    def get_text(self):
        return self.indent('exit()')



#============= EOF =============================================
