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
import os

import yaml

try:
    Loader = yaml.FullLoader
except AttributeError:
    Loader = yaml.Loader


def yload(stream, default=None, reraise=False):
    if default is None:
        default = {}

    if isinstance(stream, str) and os.path.isfile(stream):
        with open(stream, "r") as rfile:
            try:
                yd = yaml.load(rfile, Loader=Loader)
            except yaml.YAMLError as e:
                yd = default
                if reraise:
                    raise e
    else:
        try:
            yd = yaml.load(stream, Loader=Loader)
        except yaml.YAMLError as e:
            yd = default
            if reraise:
                raise e

    if yd == stream:
        yd = default

    return yd


# ============= EOF =============================================
