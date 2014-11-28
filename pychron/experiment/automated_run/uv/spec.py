# ===============================================================================
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
# ===============================================================================

#============= enthought library imports =======================
from traits.api import Str, Button, List, CStr, Property
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.experiment.automated_run.spec import AutomatedRunSpec
from pychron.experiment.automated_run.uv.automated_run import UVAutomatedRun
from pychron.pychron_constants import NULL_STR


class UVAutomatedRunSpec(AutomatedRunSpec):
    mask = CStr
    attenuator = CStr
    reprate = CStr
    #masks = Property
    extract_units_names = List([NULL_STR, 'burst', 'continuous'])
    _default_extract_units = 'burst'
    browser_button = Button('Browse')
    image = Str

    mask_position=Property(depends_on='mask')
    mask_name=Property(depends_on='mask')
    run_klass = UVAutomatedRun

    def _get_mask_position(self):
        try:
            return float(self.mask)
        except:
            return 0

    def _get_mask_name(self):
        return self.mask
    #@cached_property
    #def _get_masks(self):
    #    p = os.path.join(paths.device_dir, 'fusions_uv', 'mask_names.txt')
    #    masks = []
    #    if os.path.isfile(p):
    #        with open(p, 'r') as fp:
    #            for lin in fp:
    #                lin = lin.strip()
    #                if not lin or lin.startswith('#'):
    #                    continue
    #                masks.append(lin)
    #
    #    return masks

    def _image_browser_factory(self):
        b = self.application.get_service('pychron.media_server.browser.MediaBrowser')
        if b is not None:
            c = self.application.get_service('pychron.media_server.client.MediaClient')
            b.client = c

        return b

    def _get_run_attrs(self):
        attrs = super(UVAutomatedRunSpec, self)._get_run_attrs()
        nattrs = ('reprate', 'mask', 'attenuator', 'image')
        return list(attrs).extend(nattrs)

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _browser_button_fired(self):
        browser = self._image_browser_factory()
        #        browser.root='images/fusions_uv'
        browser.load_remote_directory('images/fusions_uv')
        info = browser.edit_traits(view='modal_view', kind='livemodal')
        if info.result:
            self.image = browser.get_selected_image_name()

# ============= EOF =============================================
