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
from mako.template import Template
from traitsui.handler import Controller
import yaml

from pychron.core.ui import set_qt


set_qt()

from pychron.core.helpers.logger_setup import logging_setup

logging_setup('dcreator')
#============= enthought library imports =======================
from traits.api import HasTraits, Str
from traitsui.api import View, Item

#============= standard library imports ========================
#============= local library imports  ==========================


class DeviceModel(HasTraits):
    name = Str

    def make_from_file(self):
        tmp = self.get_template()

        p = '/Users/ross/Sandbox/device_creator.yaml'
        with open(p, 'r') as fp:
            yd = yaml.load(fp)
            print yd

        print tmp.render(**yd)

    def get_template(self):
        tmp = Template(filename='./device_template.txt')
        return tmp


class DeviceFactory(Controller):
    def traits_view(self):
        v = View(Item('name'))
        return v


if __name__ == '__main__':
    d = DeviceModel()
    d.make_from_file()
    # d = DeviceFactory(model=DeviceModel())
    # d.configure_traits()
#============= EOF =============================================

