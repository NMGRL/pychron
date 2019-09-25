# ===============================================================================
# Copyright 2019 Jake Ross
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
from uncertainties import nominal_value, std_dev, ufloat

from pychron.core.regression.mean_regressor import WeightedMeanRegressor, MeanRegressor
from pychron.processing.argon_calculations import calculate_flux


def mean_j(ans, use_weights, error_kind, monitor_age, lambda_k):
    if monitor_age is None:
        js = [ai.uF for ai in ans]
    else:
        js = [calculate_flux(ai.uF, monitor_age, lambda_k=lambda_k) for ai in ans]

    fs = [nominal_value(fi) for fi in js]
    es = [std_dev(fi) for fi in js]

    if use_weights:
        klass = WeightedMeanRegressor
    else:
        klass = MeanRegressor

    reg = klass(ys=fs, yserr=es, error_calc_type=error_kind)
    reg.calculate()
    av = reg.predict()
    werr = reg.predict_error(1)

    j = ufloat(av, werr)

    return j, reg.mswd

# ============= EOF =====================================
