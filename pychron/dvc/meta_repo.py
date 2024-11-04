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
import os
import shutil
from datetime import datetime

from traits.api import Bool
from uncertainties import ufloat

from pychron.core.helpers.datetime_tools import ISO_FORMAT_STR
from pychron.core.helpers.filetools import (
    glob_list_directory,
    add_extension,
    list_directory,
)
from pychron.dvc import dvc_dump, dvc_load, repository_path, list_frozen_productions
from pychron.dvc.meta_object import (
    IrradiationGeometry,
    Chronology,
    Production,
    cached,
    Gains,
    LoadGeometry,
    MetaObjectException,
)
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.paths import paths, r_mkdir
from pychron.pychron_constants import (
    INTERFERENCE_KEYS,
    RATIO_KEYS,
    DEFAULT_MONITOR_NAME,
    DATE_FORMAT,
    NULL_STR,
)


# ============= enthought library imports =======================


def irradiation_geometry(name):
    p = os.path.join(paths.meta_root, "irradiation_holders", add_extension(name))
    return IrradiationGeometry(p)


def irradiation_geometry_holes(name):
    geom = irradiation_geometry(name)
    return geom.holes


def irradiation_chronology(name, allow_null=False):
    p = os.path.join(paths.meta_root, name, "chronology.txt")
    return Chronology(p, allow_null=allow_null)


def dump_chronology(path, doses):
    if doses is None:
        doses = []

    with open(path, "w") as wfile:
        for p, s, e in doses:
            if not isinstance(s, str):
                s = s.strftime(ISO_FORMAT_STR)
            if not isinstance(s, str):
                s = s.strftime(ISO_FORMAT_STR)
            if not isinstance(p, str):
                p = "{:0.3f}".format(p)

            line = "{},{},{}\n".format(p, s, e)
            wfile.write(line)


def gain_path(name):
    root = os.path.join(paths.meta_root, "spectrometers")
    if not os.path.isdir(root):
        os.mkdir(root)

    p = os.path.join(root, add_extension("{}.gain".format(name), ".json"))
    return p


def get_frozen_productions(repo):
    prods = {}
    for name, path in list_frozen_productions(repo):
        prods[name] = Production(path)

    return prods


def get_frozen_flux(repo, irradiation):
    path = repository_path(repo, "{}.json".format(irradiation))

    fd = {}
    if path:
        fd = dvc_load(path)
        for fi in fd.values():
            fi["j"] = ufloat(*fi["j"], tag="J")
    return fd


class MetaRepo(GitRepoManager):
    clear_cache = Bool

    @property
    def data_reduction_log_path(self):
        return os.path.join(paths.meta_root, "data_reduction_log.json")

    @property
    def data_reduction_manifest_path(self):
        return os.path.join(paths.meta_root, "dr_manifest.json")

    _cached_loads = None

    def get_data_reduction_loads(self):
        objs = self._cached_loads
        if objs is None:
            objs = dvc_load(self.data_reduction_log_path, default=[])
            self._cached_loads = objs
        return self._cached_loads

    def clear_data_reduction_loads_cache(self):
        self._cached_loads = None

    def save_data_reduction_loads(self, objs):
        eobjs = dvc_load(self.data_reduction_log_path, default=[])
        # for ei in eobjs:
        #     print(ei["name"])
        #     if not next((oi for oi in objs if oi["name"] == ei["name"]), None):
        #         print('not in objs')
        #         objs.append(ei)
        for oi in objs:
            eoi = next((ei for ei in eobjs if ei["name"] == oi["name"]), None)
            if eoi:
                for k, v in oi.items():
                    if k == "projects" and not v:
                        continue
                    eoi[k] = v

                # print('a', eoi)
                # eoi.update(oi)
                # print('b', eoi)
            else:
                eobjs.append(oi)

        eobjs = sorted(eobjs, key=lambda x: x["name"])
        ret = dvc_dump(eobjs, self.data_reduction_log_path)
        self.add(self.data_reduction_log_path, commit=False)

        return ret

    def save_data_reduction_manifest(self, manifest):
        dvc_dump(manifest, self.data_reduction_manifest_path)

    def get_data_reduction_manifest(self):
        return dvc_load(self.data_reduction_manifest_path, default=[])

        # main
        # loaded_manifest = []
        # if os.path.isfile(manifest_path):
        #     with open(manifest_path, "r") as rfile:
        #         loaded_manifest = json.load(rfile)

    def backup_data_reduction_loads(self):
        p = os.path.join(paths.meta_root, "data_reduction_log.json.bak")
        shutil.copy(self.data_reduction_log_path, p)

    def share_data_reduction_loads(self):
        self.smart_pull()
        self.add(self.data_reduction_log_path)
        self.commit("updated date reduction log")
        self.push()

    def get_correlation_ellipses(self):
        p = os.path.join(paths.meta_root, "correlation_ellipses.json")
        return dvc_load(p)

    def get_monitor_info(self, irrad, level):
        age, decay = NULL_STR, NULL_STR
        positions = self._get_level_positions(irrad, level)
        # assume all positions have same monitor_age/decay constant. Not strictly true. Potential some ambiquity but
        # will not be resolved now 8/26/18.
        if positions:
            position = positions[0]
            opt = position.get("options")
            if opt:
                age = position.get("monitor_age", NULL_STR)

            decayd = position.get("decay_constants")
            if decayd:
                decay = decayd.get("lambda_k_total", NULL_STR)

        return str(age), str(decay)

    def add_unstaged(self, *args, **kw):
        super(MetaRepo, self).add_unstaged(self.path, **kw)

    def save_gains(self, ms, gains_dict):
        p = gain_path(ms)
        dvc_dump(gains_dict, p)

        if self.add_paths(p):
            self.commit("Updated gains")

    def update_script(self, rootname, name, path_or_blob):
        self._update_text(os.path.join("scripts", rootname.lower()), name, path_or_blob)

    def update_experiment_queue(self, rootname, name, path_or_blob):
        self._update_text(
            os.path.join("experiments", rootname.lower()), name, path_or_blob
        )

    def update_level_production(self, irrad, name, prname, note=None):
        # prname = prname.replace(" ", "_")

        pathname = add_extension(prname, ".json")

        src = os.path.join(paths.meta_root, irrad, "productions", pathname)
        if os.path.isfile(src):
            self.update_productions(irrad, name, prname, note=note)
        else:
            self.warning_dialog("Invalid production name".format(prname))

    def update_level_monitor(
        self, irradiation, level, monitor_name, monitor_material, monitor_age, lambda_k
    ):
        obj, path = self.get_level_obj(irradiation, level)
        positions = self._get_level_positions(irradiation, level)

        options = {
            "monitor_name": monitor_name,
            "monitor_material": monitor_material,
            "monitor_age": monitor_age,
        }
        decay_constants = {"lambda_k_total": lambda_k, "lambda_k_total_error": 0}
        for p in positions:
            p["options"] = options
            p["decay_constants"] = decay_constants

        obj["positions"] = positions

        dvc_dump(obj, path)
        self.add(path)

    def add_production_to_irradiation(
        self, irrad, name, params, add=True, commit=False
    ):
        self.debug("adding production {} to irradiation={}".format(name, irrad))

        p = os.path.join(
            paths.meta_root, irrad, "productions", add_extension(name, ".json")
        )
        if isinstance(params, Production):
            prod = params
            prod.path = p
        else:
            prod = Production(p, new=not os.path.isfile(p))
            prod.update(params)

        prod.dump()
        if add:
            self.add(p, commit=commit)

    def add_production(self, irrad, name, obj, commit=False, add=True):
        p = self.get_production(irrad, name, force=True)

        p.attrs = attrs = INTERFERENCE_KEYS + RATIO_KEYS
        kef = lambda x: "{}_err".format(x)

        if obj:

            def values():
                return (
                    (k, getattr(obj, k), kef(k), getattr(obj, kef(k))) for k in attrs
                )

        else:

            def values():
                return ((k, 0, kef(k), 0) for k in attrs)

        for k, v, ke, e in values():
            setattr(p, k, v)
            setattr(p, ke, e)

        p.dump()
        if add:
            self.add(p.path, commit=commit)

    def update_production(self, prod, irradiation=None):
        ip = self.get_production(prod.name)
        self.debug("saving production {}".format(prod.name))

        params = prod.get_params()
        for k, v in params.items():
            self.debug("setting {}={}".format(k, v))
            setattr(ip, k, v)

        ip.note = prod.note

        self.add(ip.path, commit=False)
        self.commit("updated production {}".format(prod.name))

    def update_productions(self, irrad, level, production, note=None, add=True):
        p = os.path.join(paths.meta_root, irrad, "productions.json")

        obj = dvc_load(p)
        obj["note"] = str(note) or ""

        if level in obj:
            if obj[level] != production:
                self.debug(
                    "setting production to irrad={}, level={}, prod={}".format(
                        irrad, level, production
                    )
                )
                obj[level] = production
                dvc_dump(obj, p)

                if add:
                    self.add(p, commit=False)
        else:
            obj[level] = production
            dvc_dump(obj, p)
            if add:
                self.add(p, commit=False)

    def set_identifier(self, irradiation, level, pos, identifier):
        # p = self.get_level_path(irradiation, level)
        # jd = dvc_load(p)
        jd, p = self.get_level_obj(irradiation, level)
        positions = self._get_level_positions(irradiation, level)

        d = next((p for p in positions if p["position"] == pos), None)
        if d:
            d["identifier"] = identifier
            jd["positions"] = positions

        dvc_dump(jd, p)
        self.add(p, commit=False)

    def get_level_path(self, irrad, level):
        return os.path.join(paths.meta_root, irrad, "{}.json".format(level))

    def add_level(self, irrad, level, add=True):
        p = self.get_level_path(irrad, level)
        lv = dict(z=0, positions=[])
        dvc_dump(lv, p)
        if add:
            self.add(p, commit=False)

    def add_chronology(self, irrad, doses, add=True):
        p = os.path.join(paths.meta_root, irrad, "chronology.txt")

        dump_chronology(p, doses)
        if add:
            self.add(p, commit=False)

    def add_irradiation(self, name):
        p = os.path.join(paths.meta_root, name)
        if not os.path.isdir(p):
            os.mkdir(p)

    def add_position(self, irradiation, level, pos, add=True):
        p = self.get_level_path(irradiation, level)
        jd = dvc_load(p)
        if isinstance(jd, list):
            positions = jd
            z = 0
        else:
            positions = jd.get("positions", [])
            z = jd.get("z", 0)

        pd = next((p for p in positions if p["position"] == pos), None)
        if pd is None:
            positions.append({"position": pos, "decay_constants": {}})

        dvc_dump({"z": z, "positions": positions}, p)
        if add:
            self.add(p, commit=False)

    def add_irradiation_geometry_file(self, path):
        try:
            holder = IrradiationGeometry(path)
            if not holder.holes:
                raise BaseException
        except BaseException:
            self.warning_dialog("Invalid Irradiation Geometry file. Failed to import")
            return
        self.add_geometry_file(path)

    def make_geometry_file(self, name, holes):
        """
        holes = [(x,y,r,id), ]
        :param holes:
        :return:
        """
        root = os.path.join(paths.meta_root, "irradiation_holders")
        if not os.path.isdir(root):
            os.mkdir(root)

        path = os.path.join(root, "{}.txt".format(name))
        if not os.path.isfile(path):
            with open(path, "w") as wfile:
                lines = [",".join(map(str, h)) for h in holes]
                wfile.writelines(lines)

            self.add_geometry_file(path)

    def add_geometry_file(self, path):
        self.smart_pull()
        root = os.path.join(paths.meta_root, "irradiation_holders")
        if not os.path.isdir(root):
            os.mkdir(root)

        name = os.path.basename(path)
        dest = os.path.join(root, name)
        try:
            shutil.copyfile(path, dest)
        except shutil.SameFileError:
            pass

        self.add(dest, commit=False)
        self.commit("added irradiation geometry file {}".format(name))

        self.push()
        self.information_dialog('Irradiation Geometry "{}" added'.format(name))

    def get_load_holders(self):
        p = os.path.join(paths.meta_root, "load_holders")
        return list_directory(p, extension=".txt", remove_extension=True)

    def add_load_holder(self, name, path_or_txt, commit=False, add=True):
        p = os.path.join(paths.meta_root, "load_holders", name)
        if os.path.isfile(path_or_txt):
            shutil.copyfile(path_or_txt, p)
        else:
            with open(p, "w") as wfile:
                wfile.write(path_or_txt)
        if add:
            self.add(p, commit=commit)

    def update_level_z(self, irradiation, level, z):
        # p = self.get_level_path(irradiation, level)
        # obj = dvc_load(p)
        obj, p = self.get_level_obj(irradiation, level)

        try:
            add = obj["z"] != z
            obj["z"] = z
        except TypeError:
            obj = {"z": z, "positions": obj}
            add = True

        dvc_dump(obj, p)
        if add:
            self.add(p, commit=False)

    def remove_irradiation_position(self, irradiation, level, hole):
        # p = self.get_level_path(irradiation, level)
        # jd = dvc_load(p)
        jd, p = self.get_level_obj(irradiation, level)

        if jd:
            if isinstance(jd, list):
                positions = jd
                z = 0
            else:
                positions = jd["positions"]
                z = jd["z"]

            npositions = [ji for ji in positions if not ji["position"] == hole]
            obj = {"z": z, "positions": npositions}
            dvc_dump(obj, p)
            self.add(p, commit=False)

    def new_flux_positions(self, irradiation, level, positions, add=True):
        p = self.get_level_path(irradiation, level)
        obj = {"positions": positions, "z": 0}
        dvc_dump(obj, p)
        if add:
            self.add(p, commit=False)

    def update_flux_simple(self, irradiation, level, j, e, add=True):
        # p = self.get_level_path(irradiation, level)
        # jd = dvc_load(p)
        jd, p = self.get_level_obj(irradiation, level)

        if isinstance(jd, list):
            positions = jd
        else:
            positions = jd.get("positions")

        if positions:
            for ip in positions:
                ip["j"] = j
                ip["j_err"] = e

            dvc_dump(jd, p)
            if add:
                self.add(p, commit=False)

    def update_flux(
        self,
        irradiation,
        level,
        pos,
        identifier,
        j,
        e,
        mj=0,
        me=0,
        mmwsd=0,
        decay=None,
        position_jerr=None,
        analyses=None,
        options=None,
        add=True,
        save_predicted=True,
        jd=None,
    ):
        self.info(
            "Saving j for {}{}:{} {}, j={} +/-{}".format(
                irradiation, level, pos, identifier, j, e
            )
        )

        if options is None:
            options = {}

        if decay is None:
            decay = {}
        if analyses is None:
            analyses = []

        dump = False
        if jd is None:
            dump = True
            p = self.get_level_path(irradiation, level)
            jd = dvc_load(p)

        if isinstance(jd, list):
            positions = jd
            z = 0
        else:
            positions = jd.get("positions", [])
            z = jd.get("z", 0)

        if not save_predicted:
            j, e = 0, 0
            for p in positions:
                if p["identifier"] == identifier:
                    j, e = p.get("j", 0), p.get("j_err", 0)

        npos = {
            "position": pos,
            "j": j,
            "j_err": e,
            "mean_j": mj,
            "mean_j_err": me,
            "mean_j_mswd": mmwsd,
            "position_jerr": position_jerr,
            "decay_constants": decay,
            "identifier": identifier,
            "options": options,
            "analyses": [
                {
                    "uuid": ai.uuid,
                    "record_id": ai.record_id,
                    "is_omitted": ai.is_omitted(),
                }
                for ai in analyses
            ],
        }
        if positions:
            added = any((ji["position"] == pos for ji in positions))
            npositions = [ji if ji["position"] != pos else npos for ji in positions]
            if not added:
                npositions.append(npos)
        else:
            npositions = [npos]

        obj = {"z": z, "positions": npositions}
        if dump:
            dvc_dump(obj, p)
        else:
            jd["z"] = z
            jd["positions"] = npositions

        if add:
            self.add(p, commit=False)

    def update_chronology(self, name, doses):
        p = os.path.join(paths.meta_root, name, "chronology.txt")
        dump_chronology(p, doses)

        self.add(p, commit=False)

    def get_irradiation_holder_names(self):
        return glob_list_directory(
            os.path.join(paths.meta_root, "irradiation_holders"),
            extension=".txt",
            remove_extension=True,
        )

    def get_cocktail_irradiation(self):
        """
        example cocktail.json

        {
            "chronology": "2016-06-01 17:00:00",
            "j": 4e-4,
            "j_err": 4e-9
        }

        :return:
        """
        p = os.path.join(paths.meta_root, "cocktail.json")
        ret = dvc_load(p)
        nret = {}
        if ret:
            lines = ["1.0, {}, {}".format(ret["chronology"], ret["chronology"])]
            c = Chronology.from_lines(lines)
            nret["chronology"] = c
            nret["flux"] = ufloat(ret["j"], ret["j_err"])

        return nret

    def get_default_productions(self):
        p = os.path.join(paths.meta_root, "reactors.json")
        if not os.path.isfile(p):
            with open(p, "w") as wfile:
                from pychron.file_defaults import REACTORS_DEFAULT

                wfile.write(REACTORS_DEFAULT)

        return dvc_load(p)

    def get_flux_history(self, irradiation, level, **kw):
        greps = ["fit flux for {}{}".format(irradiation, level)]
        cs = self.get_commits_from_log(greps, **kw)
        return cs

    def get_flux_positions(self, irradiation, level):
        positions = self._get_level_positions(irradiation, level)
        return positions

    def get_level_obj(self, irradiation, level):
        p = self.get_level_path(irradiation, level)
        return dvc_load(p), p

    def get_flux(self, irradiation, level, position):
        positions = self.get_flux_positions(irradiation, level)
        return self.get_flux_from_positions(position, positions)

    def get_flux_from_positions(self, position, positions):
        j, je, pe, lambda_k = 0, 0, 0, None
        monitor_name, monitor_material, monitor_age = (
            DEFAULT_MONITOR_NAME,
            "sanidine",
            ufloat(28.201, 0),
        )
        if positions:
            pos = next((p for p in positions if p["position"] == position), None)
            if pos:
                j, je, pe = (
                    pos.get("j", 0),
                    pos.get("j_err", 0),
                    pos.get("position_jerr", 0),
                )
                dc = pos.get("decay_constants")
                if dc:
                    # this was a temporary fix and likely can be removed
                    if isinstance(dc, float):
                        v, e = dc, 0
                    else:
                        v, e = dc.get("lambda_k_total", 0), dc.get(
                            "lambda_k_total_error", 0
                        )
                    lambda_k = ufloat(v, e)
                mon = pos.get("monitor")
                if mon:
                    monitor_name = mon.get("name", DEFAULT_MONITOR_NAME)
                    sa = mon.get("age", 28.201)
                    se = mon.get("error", 0)
                    monitor_age = ufloat(sa, se, tag="monitor_age")
                    monitor_material = mon.get("material", "sanidine")

        fd = {
            "j": ufloat(j, je, tag="J"),
            "position_jerr": pe,
            "lambda_k": lambda_k,
            "monitor_name": monitor_name,
            "monitor_material": monitor_material,
            "monitor_age": monitor_age,
        }
        return fd

    def get_gains(self, name):
        g = self.get_gain_obj(name)
        return g.gains

    def save_sensitivities(self, sens):
        ps = []
        for k, v in sens.items():
            root = os.path.join(paths.meta_root, "spectrometers")
            p = os.path.join(root, add_extension("{}.sens".format(k), ".json"))
            dvc_dump(v, p)
            ps.append(p)

        if self.add_paths(ps):
            self.commit("Updated sensitivity")

    def get_sensitivities(self):
        specs = {}
        root = os.path.join(paths.meta_root, "spectrometers")
        for p in list_directory(root):
            if p.endswith(".sens.json"):
                name = p.split(".")[0]
                p = os.path.join(root, p)
                obj = dvc_load(p)

                for r in obj:
                    if r["create_date"]:
                        r["create_date"] = datetime.strptime(
                            r["create_date"], DATE_FORMAT
                        )
                specs[name] = obj

        return specs

    def get_sensitivity(self, name):
        sens = self.get_sensitivities()
        spec = sens.get(name)
        v = 1
        if spec:
            # get most recent sensitivity
            record = spec[-1]

            v = record.get("sensitivity", 1)
        return v

    @cached("clear_cache")
    def get_gain_obj(self, name, **kw):
        p = gain_path(name)
        return Gains(p)

    # @cached('clear_cache')
    def get_production(self, irrad, level, allow_null=False, **kw):
        iroot = os.path.join(paths.meta_root, irrad)
        if not os.path.isdir(iroot):
            self.warning(
                "The irradiation {} does not exist. Please check your Database and MetaRepo for "
                "typos".format(irrad)
            )

        ppath = os.path.join(iroot, "productions.json")
        obj = dvc_load(ppath)
        try:
            pname = obj[level]
        except KeyError:
            pname = ""
            self.warning(
                'The irradiation level "{}" is not listed in your {}/productions.json file'.format(
                    level, irrad
                )
            )

        p = os.path.join(
            paths.meta_root, irrad, "productions", add_extension(pname, ext=".json")
        )

        ip = Production(p, allow_null=allow_null)
        # print 'new production id={}, name={}, irrad={}, level={}'.format(id(ip), pname, irrad, level)
        return pname, ip

    # @cached('clear_cache')
    def get_chronology(self, name, allow_null=False, **kw):
        chron = None
        try:
            chron = irradiation_chronology(name, allow_null=allow_null)
            if self.application:
                chron.use_irradiation_endtime = self.application.get_boolean_preference(
                    "pychron.arar.constants.use_irradiation_endtime", False
                )
        except MetaObjectException:
            if name != "NoIrradiation" and not name.startswith("Package"):
                self.warning(
                    'Could not locate the irradiation chronology "{}"'.format(name)
                )
        return chron

    @cached("clear_cache")
    def get_irradiation_holder_holes(self, name, **kw):
        return irradiation_geometry_holes(name)

    @cached("clear_cache")
    def get_load_holder_holes(self, name, **kw):
        p = os.path.join(paths.meta_root, "load_holders", add_extension(name))
        holder = LoadGeometry(p)
        return holder.holes

    @property
    def sensitivity_path(self):
        return os.path.join(paths.meta_root, "sensitivity.json")

    # private
    def _get_level_positions(self, irrad, level):
        obj, p = self.get_level_obj(irrad, level)
        if isinstance(obj, list):
            positions = obj
        else:
            positions = obj.get("positions", [])
        return positions

    def _update_text(self, tag, name, path_or_blob):
        if not name:
            self.debug(
                "cannot update text with no name. tag={} name={}".format(tag, name)
            )
            return

        root = os.path.join(paths.meta_root, tag)
        if not os.path.isdir(root):
            r_mkdir(root)

        p = os.path.join(root, name)
        if os.path.isfile(path_or_blob):
            shutil.copyfile(path_or_blob, p)
        else:
            with open(p, "w") as wfile:
                wfile.write(path_or_blob)

        self.add(p, commit=False)


# ============= EOF =============================================
