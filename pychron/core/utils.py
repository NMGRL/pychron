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
from collections import namedtuple


def autodoc_helper(name, bases):
    try:
        return type(name, bases, {})
    except TypeError as e:
        return type(name)


def get_display_size():
    size = namedtuple('Size', 'width height')
    from pyface.qt.QtGui import QApplication
    desktop = QApplication.desktop()
    rect = desktop.screenGeometry()
    w, h = rect.width(), rect.height()

    return size(w, h)


# adapted from https://codereview.stackexchange.com/questions/182733/base-26-letters-and-base-10-using-recursion

BASE = 26
A_UPPERCASE = ord('A')


def alphas(n):
    a = ''
    if n is not None and n >= 0:
        if n>0:
            def decompose(n):
                while n:
                    n, rem = divmod(n, BASE)
                    yield rem

            digits = reversed([chr(A_UPPERCASE + part) for part in decompose(n)])
            a = ''.join(digits)
        else:
            a = 'A'
    return a


def alpha_to_int(l):
    return sum((ord(li) - A_UPPERCASE) * BASE ** i for i, li in enumerate(reversed(l.upper())))
