#!/usr/bin/python
# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
# ============= standard library imports ========================
from __future__ import absolute_import

from dataclasses import dataclass

# ============= local library imports  ==========================
from pychron.config_mixin import ConfigMixin


@dataclass
class BootstrapResult:
    name: str
    loaded: bool = False
    opened: bool = False
    initialized: object = False
    post_initialized: bool = False
    failed_phase: str = ""
    error: str = ""

    @property
    def success(self):
        return (
            self.loaded
            and self.opened
            and self.initialized is True
            and self.post_initialized
        )

    @property
    def compatible_success(self):
        return self.loaded and self.initialized is True

    @property
    def is_partial(self):
        return self.loaded and not self.success

    def summary(self):
        state = []
        for key in ("loaded", "opened", "initialized", "post_initialized"):
            state.append("{}={}".format(key, getattr(self, key)))
        if self.failed_phase:
            state.append("failed_phase={}".format(self.failed_phase))
        if self.error:
            state.append("error={}".format(self.error))
        return ", ".join(state)


class BaseConfigLoadable(ConfigMixin):
    """ """

    last_bootstrap_result = None

    def update_configuration(self, **kw):
        config = self.get_configuration()
        for section, options in kw.items():
            if not config.has_section(section):
                config.add_section(section)

            for option, value in options.items():
                config.set(section, option, value)
        self.write_configuration(config)

    def bootstrap(self, *args, **kw):
        return self.bootstrap_result(*args, **kw).compatible_success

    def bootstrap_result(self, *args, **kw):
        run_post_initialize = kw.pop("run_post_initialize", False)
        result = BootstrapResult(name=getattr(self, "name", self.__class__.__name__))
        self.last_bootstrap_result = result

        self._bootstrap_info("load")
        try:
            result.loaded = bool(self.load(*args, **kw))
        except BaseException as e:
            result.failed_phase = "load"
            result.error = str(e)
            self._bootstrap_exception("load", e)
            return result

        if not result.loaded:
            result.failed_phase = "load"
            self._bootstrap_warning("failed loading")
            return result

        self._bootstrap_info("open")
        try:
            result.opened = bool(self.open(*args, **kw))
        except BaseException as e:
            result.failed_phase = "open"
            result.error = str(e)
            self._bootstrap_exception("open", e)
            return result

        if not result.opened:
            self._bootstrap_warning("failed opening")

        self._bootstrap_info("initialize")
        try:
            result.initialized = self.initialize(*args, **kw)
        except BaseException as e:
            result.failed_phase = "initialize"
            result.error = str(e)
            self._bootstrap_exception("initialize", e)
            return result

        if result.initialized is None:
            result.failed_phase = "initialize"
            result.error = "initialize returned None"
            return result

        if not run_post_initialize:
            result.post_initialized = True
            return result

        self._bootstrap_info("post initialize")
        try:
            self.post_initialize(*args, **kw)
            result.post_initialized = True
        except BaseException as e:
            result.failed_phase = "post_initialize"
            result.error = str(e)
            self._bootstrap_exception("post initialize", e)

        return result

    def open(self, *args, **kw):
        """ """

        return True

    def load(self, *args, **kw):
        """ """
        return True

    def load_additional_args(self, *args, **kw):
        return True

    def _load_hook(self, config):
        pass

    def initialize(self, *args, **kw):
        """ """

        return True

    def post_initialize(self, *args, **kw):
        return True

    def convert_config_name(self, name):
        """ """
        nname = ""
        if "_" in name:
            for s in name.split("_"):
                if s == "co2":
                    s = "CO2"
                else:
                    s = s.capitalize()
                nname += s
        else:
            nname = name
        return nname

    def _bootstrap_info(self, msg):
        if hasattr(self, "info"):
            self.info(msg)

    def _bootstrap_warning(self, msg):
        if hasattr(self, "warning"):
            self.warning(msg)

    def _bootstrap_exception(self, phase, exc):
        self._bootstrap_warning("{} failed. {}".format(phase, exc))
        if hasattr(self, "debug_exception"):
            self.debug_exception()


# ============= EOF =============================================
