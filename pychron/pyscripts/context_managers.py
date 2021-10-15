# ===============================================================================
# Copyright 2019 ross
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


class RecordingCTX(object):
    def __init__(self, script, name):
        self._script = script
        self._name = name

    def __enter__(self, *args, **kw):
        self._script.start_video_recording(self._name)

    def __exit__(self, *args, **kw):
        self._script.stop_video_recording()


class LightingCTX(object):
    def __init__(self, script, value):
        self._script = script
        self._value = value

    def __enter__(self, *args, **kw):
        self._script.set_light(self._value)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._script.set_light(0)


class GrainPolygonCTX(object):
    def __init__(self, script):
        self._script = script

    def __enter__(self, *args, **kw):
        self._script.start_grain_polygon()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._script.stop_grain_polygon()

# ============= EOF =============================================
