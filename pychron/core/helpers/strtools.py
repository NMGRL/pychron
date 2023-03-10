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
# ============= standard library imports ========================
# ============= local library imports  ==========================
def ps(t):
    return "{}s".format(t)


def camel_case(name, delimiters=None):
    if delimiters is None:
        delimiters = ("_", "/", " ")

    name = "{}{}".format(name[0].upper(), name[1:])
    for d in delimiters:
        if d in name:
            name = "".join(a.title() for a in name.split(d))

    return name


def to_list(a, delimiter=",", mapping=None):
    if a is not None:
        la = a.split(delimiter)
        if mapping:
            la = [mapping[li] for li in la]

        return la


def to_terminator(t):
    if t == "\n" or "\\n" or t == "chr(10)":
        t = chr(10)
    elif t == "\r" or t == "\\r" or t == "char(13)":
        t = chr(13)

    return t


def to_bool(a):
    """
    a: a str or bool object

    if a is string
        'true', 't', 'yes', 'y', '1', 'ok' ==> True
        'false', 'f', 'no', 'n', '0' ==> False
    """

    if isinstance(a, bool):
        return a
    elif a is None:
        return False
    elif isinstance(a, (int, float)):
        return bool(a)

    tks = ["true", "t", "yes", "y", "1", "ok", "open"]
    fks = ["false", "f", "no", "n", "0", "closed"]

    # if a is not None:
    #     a = str(a).strip().lower()

    a = str(a).strip().lower()
    if a in tks:
        return True
    elif a in fks:
        return False
    else:
        return False


def csv_to_floats(*args, **kw):
    return csv_to_cast(float, *args, **kw)


def csv_to_ints(*args, **kw):
    return csv_to_cast(int, *args, **kw)


def csv_to_cast(cast, a, delimiter=","):
    return [cast(ai) for ai in a.split(delimiter)]


def to_csv_str(iterable, delimiter=","):
    return delimiter.join([str(v) for v in iterable])


def ratio(xs, ys=None, invert=False):
    def r(a, b):
        return "{}/{}".format(a, b)

    if ys is None:
        ys = xs

    if invert:
        xs = xs[::-1]
        ys = ys[::-1]

    ret = []
    for iso in xs:
        for jiso in ys:
            if iso == jiso:
                continue
            if r(jiso, iso) not in ret:
                ret.append(r(iso, jiso))

    return ret


def get_case_insensitive(d, key, default=None):
    v = None
    for k in (key, key.lower(), key.upper(), key.capitalize()):
        try:
            v = d[k]
            break
        except KeyError:
            continue

    if v is None:
        v = default
    return v


def to_int(i):
    try:
        i = int(i)
    except ValueError:
        pass
    return i


def streq(a, b):
    return a and b and a.casefold() == b.casefold()


if __name__ == "__main__":
    for ret in ratio("abc"):
        print(ret)
# ============= EOF =============================================
