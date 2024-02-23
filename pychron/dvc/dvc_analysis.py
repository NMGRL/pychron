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
import datetime
import os
import time
from operator import itemgetter

from uncertainties import ufloat, std_dev, nominal_value

from pychron.core.helpers.binpack import unpack, format_blob, encode_blob
from pychron.core.helpers.datetime_tools import make_timef
from pychron.core.helpers.filetools import add_extension
from pychron.core.helpers.iterfuncs import partition
from pychron.core.helpers.strtools import to_csv_str
from pychron.dvc import (
    USE_GIT_TAGGING,
    INTERCEPTS,
    BASELINES,
    BLANKS,
    ICFACTORS,
    PEAKCENTER,
    COSMOGENIC,
)
from pychron.dvc import (
    dvc_dump,
    dvc_load,
    analysis_path,
    make_ref_list,
    get_spec_sha,
    get_masses,
    repository_path,
    AnalysisNotAnvailableError,
)
from pychron.experiment.utilities.environmentals import set_environmentals
from pychron.experiment.utilities.runid import make_aliquot_step, make_step
from pychron.processing.analyses.analysis import Analysis
from pychron.processing.isotope import Isotope
from pychron.pychron_constants import (
    INTERFERENCE_KEYS,
    NULL_STR,
    ARAR_MAPPING,
    EXTRACTION_ATTRS,
    META_ATTRS,
    NO_BLANK_CORRECT,
    DATE_FORMAT,
    EXPONENTIAL,
)


class Blank:
    pass


class Baseline:
    pass


class TIsotope:
    def __init__(self, name, det):
        self.name = name
        self.detector = det
        self.blank = Blank()
        self.baseline = Baseline()

    def set_fit(self, *args, **kw):
        pass

    def get_intensity(self):
        return ufloat((1, 0.5))


class DVCAnalysis(Analysis):
    production_obj = None
    chronology_obj = None
    use_repository_suffix = False

    def __init__(self, uuid, record_id, repository_identifier, *args, **kw):
        super(DVCAnalysis, self).__init__(*args, **kw)
        self.record_id = record_id
        path = analysis_path((uuid, record_id), repository_identifier)
        self.repository_identifier = repository_identifier
        self.rundate = datetime.datetime.now()

        if path is None:
            raise AnalysisNotAnvailableError(repository_identifier, record_id)

        root = os.path.dirname(path)
        bname = os.path.basename(path)
        head, ext = os.path.splitext(bname)

        ep = os.path.join(root, "extraction", "{}.extr{}".format(head, ext))
        if os.path.isfile(ep):
            jd = dvc_load(ep)

            self.load_extraction(jd)

        else:
            self.warning(
                'Invalid analysis. RunID="{}". No extraction file {}'.format(
                    record_id, ep
                )
            )

        if os.path.isfile(path):
            jd = dvc_load(path)
            self.load_spectrometer_parameters(jd.get("spec_sha"))
            self.load_environmentals(jd.get("environmental"))

            self.load_meta(jd)
        else:
            self.warning(
                'Invalid analysis. RunID="{}". No meta file {}'.format(record_id, path)
            )

        self.load_paths()

    @property
    def irradiation_position_position(self):
        return self.irradiation_position

    def load_meta(self, jd):
        self.measurement_script_name = jd.get("measurement", NULL_STR)
        self.extraction_script_name = jd.get("extraction", NULL_STR)

        src = jd.get("source")
        if src:
            self.filament_parameters = src

        for attr in META_ATTRS:
            v = jd.get(attr)
            # print 'attr={},{}'.format(attr, v)
            if v is not None:
                setattr(self, attr, v)

        if self.increment is not None:
            self.step = make_step(self.increment)

        ts = jd["timestamp"]
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", DATE_FORMAT):
            try:
                self.rundate = datetime.datetime.strptime(ts, fmt)
                break
            except ValueError:
                continue

        self.timestamp = self.timestampf = make_timef(self.rundate)
        self.aliquot_step_str = make_aliquot_step(self.aliquot, self.step)

        # self.collection_version = jd['collection_version']
        self._set_isotopes(jd)

        if self.analysis_type.lower() == "sample" or not self.analysis_type:
            self.analysis_type = "unknown"
        self.arar_mapping = jd.get("arar_mapping", ARAR_MAPPING)

    def load_extraction(self, jd):
        for attr in EXTRACTION_ATTRS:
            tag = attr
            if attr == "cleanup_duration":
                if attr not in jd:
                    tag = "cleanup"
            elif attr == "extract_duration":
                if attr not in jd:
                    tag = "duration"

            v = jd.get(tag)
            if v is not None:
                setattr(self, attr, v)

        rs = jd.get("measured_response")
        if rs is None:
            rs = jd.get("request")
        self.measured_response_stream = rs

        rs = jd.get("requested_output")
        if rs is None:
            rs = jd.get("response")
        self.requested_output_stream = rs

        rs = jd.get("setpoint_stream")
        if rs is None:
            rs = jd.get("sblob")
        self.setpoint_stream = rs

        pd = jd.get("positions")
        if pd:
            pd = [p for p in pd if p]
            if pd:
                ps = sorted(pd, key=itemgetter("position"))
                self.position = to_csv_str([pp["position"] for pp in ps])
                self.xyz_position = to_csv_str(
                    [
                        "{},{},{}".format(pp["x"], pp["y"], pp["z"])
                        for pp in ps
                        if pp["x"] is not None
                    ],
                    delimiter=";",
                )
        if not self.extract_units:
            self.extract_units = "W"

    def load_environmentals(self, ed):
        if ed is not None:
            set_environmentals(self, ed)

    def load_paths(self, modifiers=None):
        if modifiers is None:
            modifiers = (
                INTERCEPTS,
                BASELINES,
                BLANKS,
                ICFACTORS,
                PEAKCENTER,
                COSMOGENIC,
            )

        if USE_GIT_TAGGING:
            modifiers += ("tags",)

        for modifier in modifiers:
            path = self._analysis_path(modifier=modifier)
            if path:
                if os.path.isfile(path):
                    jd = dvc_load(path)
                    if jd:
                        func = getattr(self, "_load_{}".format(modifier))
                        try:
                            func(jd)
                        except BaseException as e:
                            self.warning(
                                "Failed loading {}. path={}. error={}".format(
                                    modifier, path, e
                                )
                            )
                            import traceback

                            self.debug(traceback.format_exc())
                    else:
                        self.debug("path is empty. {}".format(path))
                else:
                    self.debug("Non-existent path. {}".format(path))

    def load_spectrometer_parameters(self, spec_sha):
        if spec_sha:
            name = add_extension(spec_sha, ".json")
            p = repository_path(self.repository_identifier, name)
            sd = get_spec_sha(p)
            self.source_parameters = sd["spectrometer"]
            self.gains = sd["gains"]
            self.deflections = sd["deflections"]

    def check_has_n(self):
        return any((i._n is not None for i in self.iter_isotopes()))

    def get_extraction_data(self):
        path = self._analysis_path(modifier="extraction")
        jd = dvc_load(path)
        return jd

    def load_raw_data(self, keys=None, n_only=False, use_name_pairs=True, force=False):
        self.debug(
            "loading raw data, keys={}, n_only={}, use_name_pairs={}, force={}".format(
                keys, n_only, use_name_pairs, force
            )
        )
        if self.has_raw_data and not force:
            self.debug("already has raw data {}, {}".format(self.has_raw_data, force))
            print(self.isotopes["Ar40"].sniff.xs)
            return

        path = self._analysis_path(modifier=".data")

        jd = dvc_load(path)

        signals = jd.get("signals", [])
        baselines = jd.get("baselines", [])
        sniffs = jd.get("sniffs", [])

        for sd in signals:
            isok = sd.get("isotope")
            det = sd.get("detector")

            if isok is None or det is None:
                continue

            key = isok
            if use_name_pairs:
                key = "{}{}".format(isok, det)

            if keys and key not in keys and isok not in keys:
                continue

            iso = self.get_isotope(name=isok, detector=det)
            if not iso:
                continue

            blob = sd.get("blob")
            if blob:
                iso.unpack_data(format_blob(blob), n_only)

            # det = sd['detector']
            bd = next((b for b in baselines if b.get("detector") == det), None)
            if bd:
                blob = bd.get("blob")
                if blob:
                    iso.baseline.unpack_data(format_blob(blob), n_only)

        # loop thru keys to make sure none were missed this can happen when only loading baseline
        if keys:
            for k in keys:
                bd = next((b for b in baselines if b.get("detector") == k), None)
                if bd:
                    for iso in self.itervalues():
                        if iso.detector == k:
                            blob = bd.get("blob")
                            if blob:
                                iso.baseline.unpack_data(format_blob(blob), n_only)

        for sn in sniffs:
            isok = sn.get("isotope")
            det = sn.get("detector")
            # if use_name_pairs:
            #     isok = '{}{}'.format(isok, det)

            key = isok
            if use_name_pairs:
                key = "{}{}".format(isok, det)

            if keys and key not in keys and isok not in keys:
                continue

            data = None
            blob = sn.get("blob")
            if blob:
                data = format_blob(blob)

            for iso in self.itervalues():
                if iso.detector == det:
                    iso.sniff.unpack_data(data, n_only)

        if not n_only and not keys:
            self.has_raw_data = True

    def set_production(self, prod, r):
        self.production_obj = r
        self.production_name = prod
        self.production_ratios = r.to_dict(("Ca_K", "Cl_K"))
        self.interference_corrections = r.to_dict(INTERFERENCE_KEYS)

    def set_chronology(self, chron):
        analts = self.rundate

        def convert_days(x):
            return x.total_seconds() / (60.0 * 60 * 24)

        doses = chron.get_doses()

        def calc_ti(st, en):
            t = st
            if chron.use_irradiation_endtime:
                t = en
            return convert_days(analts - t)

        segments = [
            (pwr, convert_days(en - st), calc_ti(st, en), st, en)
            for pwr, st, en in doses
            if st is not None and en is not None
        ]
        d_o = 0
        if doses:
            d_o = doses[0][1]
        self.irradiation_time = time.mktime(d_o.timetuple()) if d_o else 0

        self.chron_segments = segments
        # self.chron_dosages = doses
        self.calculate_decay_factors()

    def set_fits(self, fitobjs):
        isos = self.isotopes
        for fi in fitobjs:
            try:
                iso = isos[fi.name]
            except KeyError:
                # print 'set fits {} {}'.format(fi.name, isos.keys())
                # name is a detector
                for i in self.itervalues():
                    if i.detector == fi.name:
                        i.baseline.set_fit(fi)

                continue

            iso.set_fit(fi)

    def get_json(self, modifier):
        return self._get_json(modifier)

    def get_meta(self):
        return dvc_load(self.meta_path)

    def dump_meta(self, meta):
        dvc_dump(meta, self.meta_path)

    def dump_equilibration(self, keys, reviewed=False):
        path = self._analysis_path(modifier=".data")

        jd = dvc_load(path)
        endianness = jd["format"][0]

        nsignals = []
        nsniffs = []

        for new, existing in ((nsignals, "signals"), (nsniffs, "sniffs")):
            for sig in jd[existing]:
                key = sig["isotope"]
                if key in keys:
                    iso = self.get_isotope(key)
                    if existing == "sniffs":
                        iso = iso.sniff

                    sblob = encode_blob(iso.pack(endianness, as_hex=False))
                    new.append(
                        {"isotope": iso.name, "blob": sblob, "detector": iso.detector}
                    )
                else:
                    new.append(sig)

        for k in keys:
            # check to make sure signals/sniffs fully populated
            for new, issniff in ((nsignals, False), (nsniffs, True)):
                if not next((n for n in new if n["isotope"] == k), None):
                    iso = self.get_isotope(key)
                    if issniff:
                        iso = iso.sniff

                    sblob = encode_blob(iso.pack(endianness, as_hex=False))
                    new.append(
                        {"isotope": iso.name, "blob": sblob, "detector": iso.detector}
                    )
        jd["reviewed"] = reviewed
        jd["signals"] = nsignals
        jd["sniffs"] = nsniffs
        dvc_dump(jd, path)

        return path

    def dump_fits(self, keys, reviewed=False):
        sisos = self.isotopes
        isoks, dks = list(map(tuple, partition(keys, lambda x: x in sisos)))

        def update(d, i):
            d.update(
                fit=i.fit,
                error_type=i.error_type,
                value=float(i.value),
                error=float(i.error),
                n=i.n,
                fn=i.fn,
                reviewed=reviewed,
                include_baseline_error=i.include_baseline_error,
                filter_outliers_dict=i.filter_outliers_dict,
                user_excluded=i.user_excluded,
                outlier_excluded=i.outlier_excluded,
            )

        # save intercepts
        if isoks:
            isos, path = self._get_json(INTERCEPTS)
            if isos:
                for k in isoks:
                    try:
                        iso = isos[k]
                    except KeyError:
                        iso = {}
                        isos[k] = iso

                    siso = sisos[k]
                    if siso:
                        update(iso, siso)

                self._dump(isos, path)
            else:
                self.debug("failed locating intercepts for {}".format(self))

        # save baselines
        if dks:
            baselines, path = self._get_json(BASELINES)
            if baselines:
                for di in dks:
                    try:
                        det = baselines[di]
                    except KeyError:
                        det = {}
                        baselines[di] = det

                    # bs = next((iso.baseline for iso in six.itervalues(sisos) if iso.detector == di), None)
                    bs = self.get_isotope(detector=di, kind="baseline")
                    if bs:
                        update(det, bs)

                self._dump(baselines, path)
            else:
                self.debug("failed locating baselines for {}".format(self))

    def dump_blanks(self, keys, refs=None, reviewed=False):
        isos, path = self._get_json(BLANKS)
        sisos = self.isotopes

        for k in keys:
            if isinstance(isos, dict):
                blank = isos.get(k, {})
            else:
                blank = {}

            if k in sisos:
                siso = sisos[k]
                if siso.temporary_blank is not None:
                    blank["value"] = v = float(siso.temporary_blank.value)
                    blank["error"] = e = float(siso.temporary_blank.error)
                    blank["fit"] = f = siso.temporary_blank.fit
                    blank["references"] = make_ref_list(refs)
                    blank["reviewed"] = reviewed
                    isos[k] = blank

                    siso.blank.value = v
                    siso.blank.error = e
                    siso.blank.fit = f

        self._dump(isos, path)

    def delete_icfactors(self, dkeys):
        jd, path = self._get_json(ICFACTORS)

        remove = []
        for k in jd:
            if k not in dkeys:
                remove.append(k)

        for r in remove:
            jd.pop(r)

        self._dump(jd, path)

    def dump_icfactors(
        self,
        dkeys,
        fits,
        refs=None,
        reviewed=False,
        standard_ratios=None,
        reference_data=None,
    ):
        jd, path = self._get_json(ICFACTORS)

        for i, (dk, fi) in enumerate(zip(dkeys, fits)):
            ticf = self.temporary_ic_factors.get(dk)
            v = ticf["value"]
            if v is None:
                v, e = 1, 0
            else:
                v, e = nominal_value(v), std_dev(v)

            # hack for peakhopped data
            if ":" in dk:
                _, dk = dk.split(":")

            standard_ratio = None
            if standard_ratios:
                try:
                    standard_ratio = standard_ratios[i]
                except IndexError:
                    standard_ratio = None
            rd = None
            if reference_data:
                rd = reference_data[dk]

            jd[dk] = {}
            jd[dk].update(**ticf)

            jd[dk].update(
                **{
                    "value": float(v),
                    "error": float(e),
                    "reviewed": reviewed,
                    "fit": fi,
                    # "reference_detector": ticf["reference_detector"],
                    "standard_ratio": standard_ratio,
                    "references": make_ref_list(refs),
                    "reference_data": rd,
                }
            )

        self._dump(jd, path)

    def dump_source_correction_icfactors(self, refs=None, standard_ratio=None):
        jd, path = self._get_json(ICFACTORS)
        for det, ticf in self.temporary_ic_factors.items():
            value = ticf["value"]
            v, e = nominal_value(value), std_dev(value)
            jd[det] = {
                "value": float(v),
                "error": float(e),
                "reviewed": True,
                "fit": EXPONENTIAL,
                "standard_ratio": standard_ratio,
                "source_correction": True,
                "references": make_ref_list(refs),
            }
        self._dump(jd, path)

    def dump_cosmogenic(self):
        path = self._analysis_path(modifier=COSMOGENIC, mode="w")

        jd = self.arar_constants.cosmo_to_dict()
        self._dump(jd, path)

    def make_path(self, modifier):
        return self._analysis_path(modifier=modifier)

    # private
    def _load_cosmogenic(self, jd):
        self.arar_constants.cosmo_from_dict(jd)

    def _load_peakcenter(self, jd):
        refdet = jd.get("reference_detector")
        if refdet is None:
            pd = jd
            self.peak_center_data = unpack(pd["data"], jd["fmt"], decode=True)
        else:
            pd = jd[refdet]
            self.peak_center_data = unpack(pd["points"], jd["fmt"], decode=True)

            self.additional_peak_center_data = {
                k: unpack(pd["points"], jd["fmt"], decode=True)
                for k, pd in jd.items()
                if k
                not in (
                    refdet,
                    "fmt",
                    "interpolation",
                    "reference_detector",
                    "reference_isotope",
                )
            }

        self.peak_center = pd["center_dac"]
        self.peak_center_reference_detector = refdet

        interpolation = jd.get("interpolation", "cubic")
        self.peak_center_use_interpolation = bool(interpolation)
        self.peak_center_interpolation_kind = interpolation
        self.peak_center_reference_isotope = jd.get("reference_isotope")

    def _load_tags(self, jd):
        self.set_tag(jd)

    def _load_blanks(self, jd):
        for key, v in jd.items():
            if key in self.isotopes:
                i = self.isotopes[key]
                self._load_value_error(i.blank, v)
                i.blank.fit = fit = v["fit"]
                i.blank.reviewed = v.get("reviewed", False)

                if fit.lower() in ("previous", "preceding"):
                    refs = v.get("references")
                    if refs:
                        ref = refs[0]
                        try:
                            i.blank_source = ref["record_id"]
                        except KeyError:
                            i.blank_source = ref.get("runid", "")
                else:
                    i.blank_source = fit

    def _load_intercepts(self, jd):
        for iso, v in jd.items():
            if iso in self.isotopes:
                i = self.isotopes[iso]
                self._load_value_error(i, v)

                i.error_type = v.get("error_type", "SEM")
                fod = v.get("filter_outliers_dict")
                if fod:
                    i.set_filter_outliers_dict(**fod)
                i.set_fit(v["fit"], notify=False)
                i.set_user_excluded(v.get("user_excluded"))
                i.reviewed = v.get("reviewed", False)
                i.include_baseline_error = v.get("include_baseline_error", False)

    def _load_value_error(self, item, obj):
        item.use_manual_value = obj.get("use_manual_value", False)
        item.use_manual_error = obj.get("use_manual_error", False)
        if item.use_manual_value:
            item.value = obj["manual_value"]
        else:
            item.value = obj["value"]

        if item.use_manual_error:
            item.error = obj["manual_error"]
        else:
            item.error = obj["error"]

        for k in ("n", "fn"):
            if k in obj:
                setattr(item, k, obj[k])

    def _load_baselines(self, jd):
        for det, v in jd.items():
            for iso in self.itervalues():
                if iso.detector == det:
                    self._load_value_error(iso.baseline, v)

                    if "modifier_error" in v:
                        iso.baseline.error = v["modifier_error"]

                    iso.baseline.set_fit(v["fit"], notify=False)
                    fod = v.get("filter_outliers_dict")
                    if fod:
                        iso.baseline.set_filter_outliers_dict(**fod)

    def _load_icfactors(self, jd):
        for key, v in jd.items():
            if isinstance(v, dict):
                vv, ee = v["value"] or 0, v["error"] or 0
                r = v.get("reviewed")
                for iso in self.get_isotopes_for_detector(key):
                    iso.ic_factor = ufloat(vv, ee, tag="{} IC".format(iso.name))
                    iso.ic_factor_reviewed = r
                    iso.ic_factor_fit = v.get("fit")

    def _get_json(self, modifier):
        path = self._analysis_path(modifier=modifier)
        jd = dvc_load(path)
        return jd, path

    def _set_isotopes(self, jd):
        time_zero_offset = jd.get("time_zero_offset", 0)

        self.admit_delay = jd.get("admit_delay", 0)
        if self.admit_delay:
            time_zero_offset = -self.admit_delay

        isos = jd.get("isotopes")
        if not isos:
            return

        cb = (
            False
            if any(self.analysis_type.startswith(at) for at in NO_BLANK_CORRECT)
            else True
        )

        def factory(name, detector, v):
            i = Isotope(name, detector)
            i.set_units(v.get("units", "fA"))
            i.set_time_zero(time_zero_offset)
            i.set_detector_serial_id(v.get("serial_id", ""))
            i.correct_for_blank = cb
            return i

        try:
            isos = {k: factory(v["name"], v["detector"], v) for k, v in isos.items()}
        except KeyError:
            isos = {k: factory(k, v["detector"], v) for k, v in isos.items()}

        self.isotopes = isos
        masses = get_masses()
        # set mass
        for k, v in isos.items():
            v.mass = masses.get(k, 0)

    def _dump(self, obj, path=None, modifier=None):
        if path is None:
            path = self._analysis_path(modifier)

        dvc_dump(obj, path)

    def _analysis_path(self, repository_identifier=None, **kw):
        if repository_identifier is None:
            repository_identifier = self.repository_identifier
        ret = analysis_path((self.uuid, self.record_id), repository_identifier, **kw)
        if ret is None:
            if kw.get("modifier") in ("intercepts", "baselines", "blanks", "icfactors"):
                self.warning(
                    "Failed locating analysis path for uuid={}, record_id={} in {} {}".format(
                        self.uuid, self.record_id, repository_identifier, kw
                    )
                )
        return ret

    @property
    def intercepts_path(self):
        return self._analysis_path(modifier="intercepts")

    @property
    def baselines_path(self):
        return self._analysis_path(modifier="baselines")

    @property
    def blanks_path(self):
        return self._analysis_path(modifier="blanks")

    @property
    def ic_factors_path(self):
        return self._analysis_path(modifier="icfactors")

    @property
    def meta_path(self):
        return self._analysis_path()

    @property
    def tag_path(self):
        return self._analysis_path(modifier="tags")


# ============= EOF ============================================
