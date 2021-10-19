#!/usr/bin/python
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

from os import environ
from sys import argv

v = argv[1].lower()
if "username" in v:
    try:
        print(environ["GIT_ASKPASS_USERNAME"])
    except KeyError:
        exit(1)

    exit()
elif "password" in v:
    try:
        print(environ["GIT_ASKPASS_PASSWORD"])
    except KeyError:
        exit(1)

    exit()

exit(1)
# ============= EOF =============================================
