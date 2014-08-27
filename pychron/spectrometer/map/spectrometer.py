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
from traits.api import HasTraits, Instance
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.spectrometer.map.channel_select import ChannelSelect
from pychron.spectrometer.map.magnet import MapMagnet


class MapSpectrometer(HasTraits):
    channel_select = Instance(ChannelSelect)
    magnet = Instance(MapMagnet)

    def load(self):
        self.channel_select.load()
        self.magnet.load()

    def finish_loading(self):
        self.channel_select.finish_loading()
        self.magnet.finish_loading()

    def _channel_select_default(self):
        return ChannelSelect(name='ChannelSelect',
                             configuration_dir_name='MAP')

    def _magnet_default(self):
        return MapMagnet()
#============= EOF =============================================



