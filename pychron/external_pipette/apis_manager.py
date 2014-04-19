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

#============= enthought library imports =======================
from traits.api import implements, Instance, Button, Bool, Str, List

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.canvas.canvas2D.extraction_line_canvas2D import ExtractionLineCanvas2D
from pychron.external_pipette.protocol import IPipetteManager
from pychron.hardware.apis_controller import ApisController
from pychron.hardware.core.core_device import TimeoutError
from pychron.managers.manager import Manager


class InvalidPipetteError(BaseException):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'Invalid Pipette name={}'.format(self.name)

    def __str__(self):
        return repr(self)


class ApisManager(Manager):
    implements(IPipetteManager)
    controller = Instance(ApisController)

    available_pipettes = List(['1', '2'])

    #testing buttons
    test_load_1 = Button('Test Load 1')
    testing = Bool
    test_result = Str

    reload_canvas_button = Button('Reload Canvas')

    _timeout_flag = False
    canvas = Instance(ExtractionLineCanvas2D)

    def open_valve(self, name, **kw):
        ok = self.controller.open_valve(name)
        change = True
        return ok, change

    def close_valve(self, name, **kw):
        ok = self.controller.close_valve(name)
        change = True
        return ok, change

    def set_selected_explanation_item(self, name):
        pass

    def bind_preferences(self, prefid):
        pass

    def load_pipette(self, name, timeout=10, period=1):
        name = str(name)
        if not name in self.available_pipettes:
            raise InvalidPipetteError(name)

        self.controller.load_pipette(name)

        #wait for completion
        return self._loading_complete(timeout=timeout, period=period)

    def _loading_complete(self, **kw):
        if self._timeout_flag:
            return True
        else:
            return self.controller.blocking_poll('get_loading_status', **kw)

    #testing buttons
    def _test_load_1_fired(self):
        self.debug('Test load 1 fired')
        self.testing = True
        self.test_result = ''
        try:
            ret = self.load_pipette('1', timeout=3)
            self.test_result = 'OK'
        except (TimeoutError, InvalidPipetteError), e:
            self.test_result = str(e)
        # self.test_result = 'OK' if ret else 'Failed'
        self.testing = False

    def _reload_canvas_button_fired(self):
        self._load_canvas(self.canvas)
        self.canvas.request_redraw()

    def _load_canvas(self, c):
        c.load_canvas_file('apis_canvas_config.xml',
                           setup_name='apis_canvas')

    def _controller_default(self):
        return ApisController(name='apis')

    def _canvas_default(self):
        c = ExtractionLineCanvas2D(manager=self)
        self._load_canvas(c)
        return c

#============= EOF =============================================

