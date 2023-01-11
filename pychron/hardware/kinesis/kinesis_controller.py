# ===============================================================================
# Copyright 2023 ross
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
import requests

from pychron.hardware.motion_controller import MotionController


class KinesisMotionController(MotionController):
    base_url = None
    _axis_id_map = None

    def load_additional_args(self, config):
        """ """
        self._axis_id_map = {"x": 1, "y": 2, "z": 3}

        self.set_attribute(config, "base_url", "General", "base_url")
        if self.address is not None:
            return True

    def get_current_position(self, axis_id, *args, **kw):
        request = self._make_request("positions")
        resp = requests.get(request)
        if resp.status_code == 200:
            return self.parse_position_response(resp.json(), axis_id)

    def get_current_positions(self, keys):
        vs = []
        request = self._make_request("positions")
        resp = requests.get(request)
        if resp.status_code == 200:
            pos = resp.json()
            for k in keys:
                vs.append(self.parse_position_response(pos, k))

        return vs

    def linear_move(self, x, y, *args, **kw):
        request = self._make_request(f"/move/{x}/{y}")
        resp = requests.post(request)

    def parse_position_response(self, pos, axis_id):
        if isinstance(axis_id, str):
            try:
                axis_id = int(axis_id)
            except ValueError:
                axis_id = self._axis_id_map[axis_id]

        return pos[axis_id]["position"]

    def _make_request(self, tag):
        return f"{self.base_url}/{tag}"


# ============= EOF =============================================
