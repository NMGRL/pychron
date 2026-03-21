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

import glob
import os
import re
from pprint import pformat

from pychron import json
from pychron.core.helpers.filetools import subdirize, add_extension
from pychron.core.helpers.strtools import camel_case
from pychron.paths import paths
from pychron.wisc_ar_constants import WISCAR_ID_RE

__version__ = "2.1"

# changelog
# 2.1 added pre/post cleanup

USE_GIT_TAGGING = False

MASS_SPEC_REDUCED = "MASS SPEC REDUCED"
HISTORY_TAGS = (
    "TAG",
    "ISOEVO",
    "BLANKS",
    "ICFactor",
    "DEFINE EQUIL",
    MASS_SPEC_REDUCED,
    "COLLECTION",
    "IMPORT",
    "MANUAL",
)

DATA = ".data"
TAGS = "tags"
BASELINES = "baselines"
BLANKS = "blanks"
ICFACTORS = "icfactors"
INTERCEPTS = "intercepts"
PEAKCENTER = "peakcenter"
COSMOGENIC = "cosmogenic"

HISTORY_PATHS = (None, DATA, BASELINES, BLANKS, ICFACTORS, INTERCEPTS, TAGS)

static = (PEAKCENTER, "extraction", "monitor")
PATH_MODIFIERS = HISTORY_PATHS + static
NPATH_MODIFIERS = (None, DATA, TAGS) + static


class DVCException(BaseException):
    def __init__(self, attr):
        self._attr = attr

    def __repr__(self):
        return "DVCException: neither DVCDatabase or MetaRepo have {}".format(
            self._attr
        )

    def __str__(self):
        return self.__repr__()


class AnalysisNotAnvailableError(BaseException):
    def __init__(self, root, runid):
        self._root = root
        self._runid = runid

    def __str__(self):
        return "Analysis Not Available. {} - {}".format(self._root, self._runid)


def dvc_dump(obj, path):
    if obj is None:
        print("no object to dump")
        return

    with open(path, "w") as wfile:
        try:
            json.dump(obj, wfile, indent=4, sort_keys=True)
        except TypeError as e:
            print("dvc dump exception. error:{}, {}".format(e, pformat(obj)))


def dvc_load(path, default=None):
    if default is None:
        ret = {}
    else:
        ret = default
    if path and os.path.isfile(path):
        with open(path, "r") as rfile:
            try:
                ret = json.load(rfile)
            except ValueError as e:
                print("dvc load exception. error: {}, {}".format(e, path))
    return ret


MASSES = None


def get_masses():
    from pychron.paths import paths

    global MASSES
    if MASSES is None:
        path = os.path.join(paths.meta_root, "molecular_weights.json")
        MASSES = dvc_load(path)

    return MASSES


SPEC_SHAS = {}


def get_spec_sha(p):
    if p not in SPEC_SHAS:
        sd = dvc_load(p)
        SPEC_SHAS[p] = sd

    return SPEC_SHAS[p]


def analysis_path(analysis, *args, **kw):
    if isinstance(analysis, tuple):
        uuid, record_id = analysis
    elif isinstance(analysis, str):
        uuid, record_id = analysis, analysis
    else:
        uuid, record_id = analysis.uuid, analysis.record_id

    # using the uuid for the path identifiers is preferred.
    # data should be saved this way. but for backwards compatibility
    # analysis paths using the record_id/runid can also be handled
    try:
        ret = _analysis_path(uuid, *args, **kw)
    except AnalysisNotAnvailableError:
        try:
            ret = _analysis_path(record_id, *args, **kw)
        except AnalysisNotAnvailableError as e:
            if kw.get("mode", "r") == "r":
                ret = None
            else:
                raise e

    return ret


UUID_RE = re.compile(
    r"^[0-9a-f]{8}\-[0-9a-f]{4}\-4[0-9a-f]{3}\-[89ab][0-9a-f]{3}\-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _analysis_path(
    runid,
    repository,
    modifier=None,
    extension=".json",
    mode="r",
    root=None,
    is_temp=False,
    force_sublen=False,
):
    runid = runid.replace(":", "_")

    if root is None:
        root = paths.repository_dataset_dir

    root = os.path.join(root, repository)
    if is_temp:
        root = os.path.join(root, "temp")
        if not os.path.isdir(root):
            os.mkdir(root)

    # determine the length of dir name for subdirize
    if force_sublen:
        sublen = force_sublen
    elif UUID_RE.match(runid):
        sublen = 5, 3, 2
    elif WISCAR_ID_RE.match(runid):
        sublen = 3
    else:
        sublen = 3
        if runid.count("-") > 1:
            args = runid.split("-")[:-1]
            if len(args[0]) == 1:
                sublen = 4
            else:
                sublen = 5

    # make sure sublen is iterable
    if isinstance(sublen, int):
        sublen = (sublen,)

    # save root as oroot.  root is reused in the loop
    oroot = root
    for si in sublen:
        try:
            root, tail = subdirize(oroot, runid, sublen=si, mode=mode)
        except TypeError as e:
            continue

        if modifier:
            d = os.path.join(root, modifier)
            if not os.path.isdir(d):
                if mode == "r":
                    raise AnalysisNotAnvailableError(root, runid)

                os.mkdir(d)

            root = d
            fmt = "{}.{}"
            if modifier.startswith("."):
                fmt = "{}{}"
            tail = fmt.format(tail, modifier[:4])

        name = add_extension(tail, extension)
        path = os.path.join(root, name)
        if mode == "r":
            if not os.path.isfile(path):
                # this can happen if there is overlap in the subdirs.
                # for example this could be the directory structure
                # cf
                #  -529ae-34de-415b-ad8c-a27567b44fd8.json
                # cff52
                #  -7ab-86e8-4ccc-a6c5-118ff07c5083.json

                # in this case pychron will fail to find cf529ae... because subdirize will use a sublen of 5 first

                # moving the sublen looping out of subdirize resolves this issue
                continue

        return path
    else:
        raise AnalysisNotAnvailableError(root, runid)


def repository_path(*args):
    return os.path.join(paths.repository_dataset_dir, *args)


# def make_ref_plot_list(refs):
#
#     xs = [for r in refs]
#     ys = [for r in refs]
#
#     return {"xs": xs, "ys": ys}


def make_ref_list(refs):
    ret = ""
    if refs:
        ret = [
            {"record_id": r.record_id, "uuid": r.uuid, "exclude": r.temp_status}
            for r in refs
        ]
    return ret


def list_frozen_productions(repo):
    ps = []
    for prod in glob.glob(repository_path(repo, "*.*.production.json")):
        name = os.path.basename(prod)
        irrad, level = name.split(".")[:2]
        name = "{}.{}".format(irrad, level)
        ps.append((name, prod))
    return ps


def prep_repo_name(name):
    # camel case and remove special characters
    name = camel_case(name)
    name = re.sub(r"[^.a-zA-Z0-9]", "-", name)

    return name


# ============= EOF =============================================
