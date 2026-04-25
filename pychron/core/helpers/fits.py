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

# ============= enthought library imports =======================
# ============= standard library imports ========================

# ============= local library imports  ==========================
import six

from pychron.pychron_constants import AUTO_LINEAR_PARABOLIC, EXPONENTIAL

FITS = ["linear", "parabolic", "cubic", "quartic"]


def fit_to_degree(f):
    return FITS.index(f.lower()) + 1


def natural_name_fit(f):
    if isinstance(f, (str, six.text_type)):
        return f
    elif isinstance(f, int):
        return FITS[max(0, f - 1)]


def convert_fit(f):
    err = "SEM"
    if isinstance(f, tuple):
        f, err = f
    if isinstance(f, (str, six.text_type)):
        f = f.lower()
        if "_" in f:
            try:
                f, err = f.split("_")
                err = err.upper()
            except ValueError:
                return None, None

        if f in FITS:
            f = FITS.index(f) + 1
        elif f in (
            "average",
            "weighted mean",
            EXPONENTIAL,
            AUTO_LINEAR_PARABOLIC.lower(),
        ) or f.startswith("custom:"):
            if not err:
                err = "SEM" if "sem" in f else "SD"
        else:
            f = None

    return f, err


# ============= EOF =============================================
