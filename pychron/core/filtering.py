# ===============================================================================
# Copyright 2015 Jake Ross
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

# ============= enthought library imports =======================
import re

from numpy import ma


# ============= standard library imports ========================
# ============= local library imports  ==========================


def filter_items(items, predicate_str, return_indices=True):
    omits = []
    if predicate_str:
        match = re.search(r'(?P<name>[A-Za-z])', predicate_str)
        if match:
            variable_name = match.group('name')
            omits = [(eval(predicate_str, {variable_name: yi}), i) for i, yi in enumerate(items)]
            omits = [idx for ti, idx in omits if ti]
            if not return_indices:
                omits = [items[i] for i in omits]

    return omits


regex = re.compile(r'error|percent_error|(?! and| or)[A-Za-z]+')


def validate_filter_predicate(predicate):
    attr = regex.findall(predicate)
    ctx = {}
    for ai in attr:
        ctx[ai] = 1

    try:
        eval(predicate, ctx)
        return True
    except BaseException:
        pass


def filter_ufloats(items, predicate_str, return_indices=True):
    """
    return a list of omitted indices (or values) where predicate evaluates to true

    :param items: a list of 2-tuples
    :param predicate_str: predicate to perform filtering. item is included in the returned list if predicate evaluates
    True.
    :param return_indices:
    :return: a list of omitted indices if return_indices is True or a list of omitted items
    """
    attrs = regex.findall(predicate_str)

    def make_ctx(v, e):
        ctx = {}
        for ai in attrs:
            if ai == 'error':
                ctx[ai] = e
            elif ai == 'percent_error':
                ctx[ai] = e / v * 100 if v else 0
            else:
                ctx[ai] = v
        return ctx

    omits = [(i, eval(predicate_str, make_ctx(*uf))) for i, uf in enumerate(items)]
    omits = [idx for idx, ti in omits if ti]
    if not return_indices:
        omits = [items[i] for i in omits]

    return omits


def sigma_filter(vs, nsigma):
    mean = vs.mean()
    s = vs.std()
    ds = abs(vs - mean)
    omits = ma.where(ds > (s * nsigma))[0]
    return list(omits)


if __name__ == '__main__':
    x = ma.array([1, 1, 1, 1, 1, 10], mask=False)
    x.mask[5] = True
    o = sigma_filter(x, 1)

# filter_objects([], 'x.error>10')
# print filter_ufloats([(1,1),(10,11), (20,1)], 'age>10')
# print filter_objects([(1,1),(10,11), (20,1)], 'x>10 or error>10')
# print filter_objects([(1,1),(10,1), (20,11)], 'x>10 and error>10')
# filter_objects([], 'x>10 and error>10')
# filter_objects([], 'x>10 and percent_error>10')

# print filter_items([1, 10, 20], '10<x or x<5')
# ============= EOF =============================================
