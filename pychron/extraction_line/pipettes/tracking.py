# ===============================================================================
# Copyright 2013 Jake Ross
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
from __future__ import absolute_import

import json

import six.moves.cPickle as pickle

from traits.api import Str, Int

# ============= standard library imports ========================
import os

# ============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.core.helpers.datetime_tools import generate_datetimestamp


class PipetteTracker(Loggable):
    inner = Str
    outer = Str
    counts = Int
    _shot_loaded = False

    #     def __init__(self, *args, **kw):
    #         super(PipetteTracker, self).__init__(*args, **kw)
    #         self.load()

    def check_shot(self, name):
        """
        check shot called only when valve opens
        """
        if name == self.inner:
            self._shot_loaded = True
            return True

        elif name == self.outer:
            if self._shot_loaded:
                self._increment()
                self._shot_loaded = False
                return True

    def _increment(self):
        self.counts += 1

        self.debug("increment shot count {}".format(self.counts))
        self.dump()

    # ===============================================================================
    # persistence
    # ===============================================================================
    def load(self):
        p = self._get_path_id()
        if os.path.isfile(p):
            if p.endswith(".json"):
                with open(p, "r") as rfile:
                    self._load(json.load(rfile))
            else:
                with open(p, "rb") as rfile:
                    try:
                        params = pickle.load(rfile)
                        self._load(params)
                    except (pickle.PickleError, OSError):
                        pass
        else:
            # try loading old
            p = self._get_path_id(pickled=True)
            with open(p, "rb") as rfile:
                try:
                    params = pickle.load(rfile)
                    self._load(params)
                except (pickle.PickleError, OSError):
                    pass
            self.dump()

    def dump(self):
        p = self._get_path_id()
        if p.endswith(".json"):
            with open(p, "w") as wfile:
                json.dump(self._dump(), wfile)
        else:
            with open(p, "wb") as wfile:
                pickle.dump(self._dump(), wfile)
        self.debug("saved current shot count {}".format(self.counts))

    def _load(self, params):
        if params:
            try:
                cnts = params["counts"]
                last_shot_time = params["last_shot_time"]
            except KeyError:
                cnts = 0

            self.counts = cnts
            self.debug(
                "loaded current shot count {} time:{}".format(
                    self.counts, last_shot_time
                )
            )

    def to_dict(self):
        return self._dump()

    def _dump(self):
        d = dict(counts=self.counts, last_shot_time=generate_datetimestamp())

        return d

    def _get_path_id(self, pickled=False):
        # handle legacy format
        p = os.path.join(
            paths.hidden_dir, "pipette-{}_{}".format(self.inner, self.outer)
        )
        if not os.path.isfile(p):
            name = "{}_{}-{}".format(self.name, self.inner, self.outer)
            if not pickled:
                name = "{}.json".format(name)

            p = os.path.join(paths.hidden_dir, name)

        return p


# ============= EOF =============================================
