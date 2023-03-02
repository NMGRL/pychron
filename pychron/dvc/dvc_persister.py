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

import hashlib
import os
import shutil
from datetime import datetime

from apptools.preferences.preference_binding import bind_preference
from git.exc import GitCommandError

# ============= enthought library imports =======================
from sqlalchemy.exc import OperationalError, DatabaseError
from traits.api import Instance, Bool, Str
from uncertainties import std_dev, nominal_value
from yaml import YAMLError

from pychron.core.helpers.binpack import encode_blob, pack
from pychron.core.helpers.datetime_tools import get_datetime
from pychron.core.yaml import yload
from pychron.dvc import (
    dvc_dump,
    analysis_path,
    repository_path,
    NPATH_MODIFIERS,
    INTERCEPTS,
    BLANKS,
    BASELINES,
    ICFACTORS,
)
from pychron.experiment.automated_run.persistence import BasePersister
from pychron.experiment.automated_run.persistence_spec import PersistenceSpec
from pychron.experiment.automated_run.spec import AutomatedRunSpec
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.paths import paths
from pychron.pychron_constants import (
    DVC_PROTOCOL,
    NULL_STR,
    ARGON_KEYS,
    ARAR_MAPPING,
    EXTRACTION_ATTRS,
    META_ATTRS,
    NULL_EXTRACT_DEVICES,
    POSTCLEANUP,
    PRECLEANUP,
    CLEANUP,
    EXTRACT_UNITS,
    EXTRACT_VALUE,
    DURATION,
    WEIGHT,
    CRYO_TEMP,
)


def format_repository_identifier(project):
    return project.replace("/", "_").replace("\\", "_").replace(" ", "_")


def spectrometer_sha(settings, src, defl, gains):
    sha = hashlib.sha1()
    for d in (settings, src, defl, gains):
        for k, v in sorted(d.items()):
            sha.update(k.encode("utf-8"))
            sha.update(str(v).encode("utf-8"))

    return sha.hexdigest()


class DVCPersister(BasePersister):
    active_repository = Instance(GitRepoManager)
    dvc = Instance(DVC_PROTOCOL)
    use_isotope_classifier = Bool(False)
    use_uuid_path_name = Bool(True)
    # isotope_classifier = Instance(IsotopeClassifier, ())
    stage_files = Bool(True)
    default_principal_investigator = Str
    _positions = None
    use_data_collection_branch = Bool(False)

    save_log_enabled = Bool(False)
    arar_mapping = None

    def __init__(self, bind=True, load_mapping=True, *args, **kw):
        super(DVCPersister, self).__init__(*args, **kw)
        if bind:
            bind_preference(
                self, "use_uuid_path_name", "pychron.experiment.use_uuid_path_name"
            )

            bind_preference(
                self,
                "use_data_collection_branch",
                "pychron.experiment.use_data_collection_branch",
            )

        if load_mapping:
            self._load_arar_mapping()

    def new_spec(self, **kw):
        pspec = PersistenceSpec(**kw)
        rspec = AutomatedRunSpec()
        pspec.run_spec = rspec
        return pspec

    def per_spec_save(
        self, pr, repository_identifier=None, commit=False, commit_tag=None, push=True
    ):
        self.per_spec = pr

        if repository_identifier:
            self.initialize(repository_identifier, False)

        self.pre_extraction_save()
        self.pre_measurement_save()
        self.post_extraction_save()
        self.post_measurement_save(commit=commit, commit_tag=commit_tag, push=push)

    def push(self):
        # push changes
        self.dvc.push_repository(self.active_repository)
        # push commit
        self.dvc.meta_push()

    def initialize(self, repository, pull=True):
        """
        setup git repos.

        repositories are guaranteed to exist. The automated run factory clones the required projects
        on demand.

        :return:
        """
        self.debug(
            "^^^^^^^^^^^^^ Initialize DVCPersister {} pull={}".format(repository, pull)
        )

        self.dvc.initialize()

        repository = format_repository_identifier(repository)
        self.active_repository = repo = GitRepoManager()

        root = repository_path(repository)
        repo.open_repo(root)

        remote = "origin"
        if repo.has_remote(remote) and pull:
            self.info("pulling changes from repo: {}".format(repository))
            try:
                repo.pull(
                    remote=remote,
                    use_progress=False,
                    use_auto_pull=self.dvc.use_auto_pull,
                )
            except GitCommandError:
                self.warning("failed pulling changes")
                self.debug_exception()

    def pre_extraction_save(self):
        pass

    def post_extraction_save(self):
        self.info("================= post extraction save started =================")
        per_spec = self.per_spec
        rblob = per_spec.response_blob  # time vs measured response
        oblob = per_spec.output_blob  # time vs %output
        sblob = per_spec.setpoint_blob  # time vs requested
        cblob = per_spec.cryo_response_blob  # time vs measured response

        gp = per_spec.grain_polygons

        obj = {}
        for key, blob in (
            ("measured_response", rblob),
            ("requested_output", oblob),
            ("setpoint_stream", sblob),
            ("cryo_response", cblob),
        ):
            if blob is not None:
                blob = encode_blob(blob)
            obj[key] = blob

        if gp:
            gp = [encode_blob(g) for g in gp]

        obj = {
            "snapshots": per_spec.snapshots,
            "videos": per_spec.videos,
            "grain_polygons": gp,
            "extraction_context": per_spec.extraction_context,
        }

        pid = per_spec.pid
        if pid:
            obj["pid"] = pid

        for e in EXTRACTION_ATTRS:
            v = getattr(per_spec.run_spec, e)
            obj[e] = v

        if not per_spec.positions:
            ps = [dict()]
        else:
            ps = []
            for i, pp in enumerate(per_spec.positions):
                pos, x, y, z = None, None, None, None
                if isinstance(pp, tuple):
                    if len(pp) == 2:
                        x, y = pp
                    elif len(pp) == 3:
                        x, y, z = pp
                else:
                    pos = pp
                    try:
                        ep = per_spec.extraction_positions[i]
                        x = ep[0]
                        y = ep[1]
                        if len(ep) == 3:
                            z = ep[2]
                    except IndexError:
                        self.debug("no extraction position for {}".format(pp))
                    except TypeError:
                        self.debug("invalid extraction position")

                try:
                    pos = int(pos)
                except BaseException:
                    pos = None

                pd = {
                    "x": x,
                    "y": y,
                    "z": z,
                    "position": pos,
                    "is_degas": per_spec.run_spec.identifier == "dg",
                }
                ps.append(pd)

        obj["positions"] = ps

        self._positions = ps

        hexsha = self.dvc.get_meta_head()
        obj["commit"] = str(hexsha)
        obj["pipette_counts"] = self.per_spec.pipette_counts
        obj["timestamp"] = datetime.now().isoformat()
        path = self._make_path(modifier="extraction")
        dvc_dump(obj, path)
        self.info("================= post extraction save finished =================")

    def pre_measurement_save(self):
        pass

    def post_measurement_save(
        self,
        commit=True,
        commit_tag="COLLECTION",
        push=True,
        exception_queue=None,
        complete_event=None,
    ):
        """
        save
            - analysis.json
            - analysis.monitor.json

        check if unique spectrometer.json
        commit changes
        push changes


        :return:
        """
        self.info("================= post measurement save started =================")

        ar = self.active_repository

        # save spectrometer
        spec_sha = self._get_spectrometer_sha()
        spec_path = os.path.join(ar.path, "{}.json".format(spec_sha))
        if not os.path.isfile(spec_path):
            self._save_spectrometer_file(spec_path)

        # self.dvc.meta_repo.save_gains(self.per_spec.run_spec.mass_spectrometer,
        #                               self.per_spec.gains)

        # save analysis

        if not self.per_spec.timestamp:
            timestamp = datetime.now()
        else:
            timestamp = self.per_spec.timestamp

        # check repository identifier before saving
        # will modify repository to NoRepo if repository_identifier does not exist
        self._check_repository_identifier()

        self._save_analysis(timestamp)
        dvc = self.dvc
        with dvc.session_ctx():
            try:
                self._save_analysis_db(timestamp)
            except DatabaseError as e:
                self.debug_exception()
                self.warning(e)
                if exception_queue:
                    exception_queue.put(("Fatal", "DatabaseError. see log"))

        # save monitor
        self._save_monitor()

        # save peak center
        self._save_peak_center(self.per_spec.peak_center)

        # stage files

        if self.stage_files:
            if commit:
                if self.use_data_collection_branch:
                    ar.create_branch("data_collection", inform=False, push=True)
                    try:
                        ar.checkout_branch(
                            "data_collection", inform=False, load_history=False
                        )
                    except GitCommandError:
                        ar.reset()
                        ar.checkout_branch(
                            "data_collection", inform=False, load_history=False
                        )

                    ar.smart_pull(branch="data_collection", accept_our=True)

                paths = [
                    spec_path,
                ] + [self._make_path(modifier=m) for m in NPATH_MODIFIERS]

                for p in paths:
                    if os.path.isfile(p):
                        ar.add(p, commit=False)
                    else:
                        self.debug("not at valid file {}".format(p))

                # commit files
                ar.commit("<{}>".format(commit_tag))

                # commit default data reduction
                add = False
                p = self._make_path(INTERCEPTS)
                if os.path.isfile(p):
                    ar.add(p, commit=False)
                    add = True

                p = self._make_path(BASELINES)
                if os.path.isfile(p):
                    ar.add(p, commit=False)
                    add = True

                if add:
                    ar.commit("<ISOEVO> default collection fits")

                for pp, tag, msg in (
                    (
                        "blanks",
                        "BLANKS",
                        "preceding {}".format(self.per_spec.previous_blank_runid),
                    ),
                    ("icfactors", "ICFactor", "default"),
                ):
                    p = self._make_path(pp)
                    if os.path.isfile(p):
                        ar.add(p, commit=False)
                        ar.commit("<{}> {}".format(tag, msg))
                try:
                    if push:
                        # push changes
                        dvc.push_repository(ar)
                except GitCommandError as e:
                    self.debug_exception()
                    self.warning(e)
                    if exception_queue:
                        exception_queue.put(
                            (
                                "NonFatal",
                                "NON FATAL\n\n"
                                "DVC/Git upload of analysis not successful."
                                "Do you want to CANCEL the experiment?\n",
                            )
                        )

                # update meta
                dvc.meta_pull(accept_our=True)

                dvc.meta_commit(
                    "repo updated for analysis {}".format(self.per_spec.run_spec.runid)
                )

                try:
                    if push:
                        # push commit
                        dvc.meta_push()
                except GitCommandError as e:
                    self.debug_exception()
                    self.warning(e)
                    if exception_queue:
                        exception_queue.put(
                            (
                                "NonFatal",
                                "NON FATAL\n\n"
                                "DVC/Git upload of analysis not successful."
                                "Do you want to CANCEL the experiment?\n",
                            )
                        )

        self.info("================= post measurement save finished =================")
        if complete_event:
            self.debug("clear save flag")
            complete_event.clear()

    def save_run_log_file(self, path):
        if self.save_enabled and self.save_log_enabled:
            self.debug("saving run log file")

            npath = self._make_path("logs", ".log")
            shutil.copyfile(path, npath)
            ar = self.active_repository
            ar.smart_pull(accept_our=True)
            ar.add(npath, commit=False)
            ar.commit("<COLLECTION> log")
            self.dvc.push_repository(ar)

    # private
    def _load_arar_mapping(self):
        """
        Isotope: IsotopeKey

        example arar_mapping.yaml

        {
            Ar40: 'Ar40',
            Ar39: 'Ar39',
            Ar38: 'Ar38',
            Ar37: 'Ar37',
            Ar36: 'Ar36L1'
        }

        :return:
        """
        p = os.path.join(paths.setup_dir, "arar_mapping.yaml")
        if os.path.isfile(p):
            self.debug("loading arar mapping from {}".format(p))

            # with open(p, 'r') as rfile:
            try:
                obj = yload(p)
            except YAMLError:
                obj = {}

            for k in ARGON_KEYS:
                if k not in obj:
                    self.warning(
                        "Invalid arar_mapping.yaml file. required keys={}".format(
                            ARGON_KEYS
                        )
                    )
                    return

            self.arar_mapping = obj

    def _check_repository_identifier(self):
        repo_id = self.per_spec.run_spec.repository_identifier
        db = self.dvc.db
        repo = db.get_repository(repo_id)
        if repo is None:
            self.warning('No repository named ="{}" changing to NoRepo'.format(repo_id))
            self.per_spec.run_spec.repository_identifier = "NoRepo"
            repo = db.get_repository("NoRepo")
            if repo is None:
                db.add_repository("NoRepo", self.default_principal_investigator)

    def _save_analysis_db(self, timestamp):
        ps = self.per_spec
        rs = ps.run_spec
        d = {
            k: getattr(rs, k)
            for k in (
                "uuid",
                "analysis_type",
                "aliquot",
                "increment",
                "mass_spectrometer",
                WEIGHT,
                CLEANUP,
                PRECLEANUP,
                POSTCLEANUP,
                CRYO_TEMP,
                DURATION,
                EXTRACT_VALUE,
                EXTRACT_UNITS,
            )
        }
        d["comment"] = rs.comment[:200] if rs.comment else ""

        ed = rs.extract_device
        if ed in NULL_EXTRACT_DEVICES:
            d["extract_device"] = "No Extract Device"
        else:
            d["extract_device"] = ed

        d["timestamp"] = timestamp

        # save script names
        d["measurementName"] = ps.measurement_name
        d["extractionName"] = ps.extraction_name

        d["experiment_type"] = self.per_spec.experiment_type

        db = self.dvc.db
        an = db.add_analysis(**d)
        if an is None:
            self.warning("Failed adding analysis to database. See full log for error")
            return

        # save currents
        self._save_currents(an)

        # for iso in ps.isotope_group.isotopes.values():
        #     self.add_current(iso)
        # db.add_analysis_result(an, iso)

        # save media
        if ps.snapshots:
            for p in ps.snapshots:
                db.add_media(p, an)

        if ps.videos:
            for p in ps.videos:
                db.add_media(p, an)

        if self._positions:
            if rs.load_name and rs.load_name != NULL_STR:
                load_name = rs.load_name
                load_holder = rs.load_holder

                db.add_load(load_name, load_holder, rs.username)
                db.flush()
                db.commit()

                for position in self._positions:
                    self.debug("adding measured position {}".format(position))
                    if not db.add_measured_position(an, load=load_name, **position):
                        self.warning(
                            "failed adding position {}, load={}".format(
                                position, load_name
                            )
                        )

        # all associations are handled by the ExperimentExecutor._retroactive_experiment_identifiers
        # *** _retroactive_experiment_identifiers is currently disabled ***

        if ps.use_repository_association:
            db.add_repository_association(rs.repository_identifier, an)

        self.debug('get identifier "{}"'.format(rs.identifier))
        pos = db.get_identifier(rs.identifier)
        self.debug("setting analysis irradiation position={}".format(pos))
        if pos is None:
            an.simple_identifier = int(rs.identifier)
        else:
            an.irradiation_position = pos

        t = ps.tag

        db.flush()

        change = db.add_analysis_change(tag=t)
        an.change = change

        db.commit()
        return True

    def _save_currents(self, dban):
        dvc = self.dvc
        if dvc.update_currents_enabled:
            ps = self.per_spec
            db = dvc.db

            for key, iso in ps.isotope_group.isotopes.items():
                param = db.add_parameter("{}_intercept".format(key))
                db.add_current(dban, iso.value, iso.error, param, iso.units)

                param = db.add_parameter("{}_blank".format(key), iso.blank.units)
                db.add_current(
                    dban, iso.blank.value, iso.blank.error, param, iso.blank.units
                )

                param = db.add_parameter("{}_bs_corrected".format(key))
                v = iso.get_baseline_corrected_value()
                db.add_current(dban, nominal_value(v), std_dev(v), param, iso.units)

                param = db.add_parameter("{}_ic_corrected".format(key))
                v = iso.get_ic_corrected_value()
                db.add_current(dban, nominal_value(v), std_dev(v), param, iso.units)

                param = db.add_parameter(key)
                v = iso.get_non_detector_corrected_value()
                db.add_current(dban, nominal_value(v), std_dev(v), param, iso.units)

                param = db.add_parameter(iso.baseline.name)
                db.add_current(
                    dban,
                    iso.baseline.value,
                    iso.baseline.error,
                    param,
                    iso.baseline.units,
                )

                param = db.add_parameter("{}_n".format(iso.baseline.name))
                db.add_current(dban, iso.baseline.n, None, param, "int")

                param = db.add_parameter("{}_n".format(iso.name))
                db.add_current(dban, iso.n, None, param, "int")

    def _save_analysis(self, timestamp):
        isos = {}
        dets = {}
        signals = []
        baselines = []
        sniffs = []
        blanks = {}
        intercepts = {}
        cbaselines = {}
        icfactors = {}

        endianness = ">"
        per_spec = self.per_spec

        source = {"emission": per_spec.emission, "trap": per_spec.trap}

        clf = None
        if self.use_isotope_classifier:
            clf = self.application.get_service(
                "pychron.classifier.isotope_classifier.IsotopeClassifier"
            )

        for key, iso in per_spec.isotope_group.items():
            sblob = encode_blob(iso.pack(endianness, as_hex=False))
            snblob = encode_blob(iso.sniff.pack(endianness, as_hex=False))

            for ss, blob in ((signals, sblob), (sniffs, snblob)):
                d = {"isotope": iso.name, "detector": iso.detector, "blob": blob}
                ss.append(d)

            detector = next(
                (d for d in per_spec.active_detectors if d.name == iso.detector), None
            )

            isod = {
                "detector": iso.detector,
                "name": iso.name,
                "units": detector.units if detector else "",
                "serial_id": detector.serial_id if detector else "00000",
            }

            if clf is not None:
                klass, prob = clf.predict_isotope(iso)
                isod.update(classification=klass, classification_probability=prob)

            isos[key] = isod

            if iso.detector not in dets:
                bblob = encode_blob(iso.baseline.pack(endianness, as_hex=False))
                baselines.append({"detector": iso.detector, "blob": bblob})
                dets[iso.detector] = {
                    "deflection": per_spec.defl_dict.get(iso.detector),
                    "gain": per_spec.gains.get(iso.detector),
                }

                icfactors[iso.detector] = {
                    "value": float(nominal_value(iso.ic_factor or 1)),
                    "error": float(std_dev(iso.ic_factor or 0)),
                    "fit": "default",
                    "references": [],
                }
                cbaselines[iso.detector] = {
                    "fit": iso.baseline.fit,
                    "error_type": iso.baseline.error_type,
                    "filter_outliers_dict": iso.baseline.filter_outliers_dict,
                    "value": float(iso.baseline.value),
                    "error": float(iso.baseline.error),
                }

            intercepts[key] = {
                "fit": iso.fit,
                "error_type": iso.error_type,
                "filter_outliers_dict": iso.filter_outliers_dict,
                "value": float(iso.value),
                "error": float(iso.error),
            }

            blanks[key] = {
                "fit": "previous",
                "error_type": "",
                "references": [
                    {"record_id": per_spec.previous_blank_runid, "exclude": False}
                ],
                "value": float(iso.blank.value),
                "error": float(iso.blank.error),
            }

        obj = self._make_analysis_dict()

        from pychron.version import __version__ as pversion
        from pychron.experiment import __version__ as eversion
        from pychron.dvc import __version__ as dversion

        obj["timestamp"] = timestamp.isoformat()
        if per_spec.time_zero:
            obj["time_zero_timestamp"] = get_datetime(per_spec.time_zero).isoformat()

        obj["collection_version"] = "{}:{}".format(eversion, dversion)
        obj["acquisition_software"] = "pychron {}".format(pversion)
        obj["data_reduction_software"] = "pychron {}".format(pversion)

        obj["environmental"] = {
            "lab_temperatures": per_spec.lab_temperatures,
            "lab_humiditys": per_spec.lab_humiditys,
            "lab_pneumatics": per_spec.lab_pneumatics,
        }

        obj["laboratory"] = per_spec.laboratory
        obj["instrument_name"] = per_spec.instrument_name
        obj["analyst_name"] = per_spec.run_spec.username
        obj["whiff_result"] = per_spec.whiff_result
        obj["detectors"] = dets
        obj["isotopes"] = isos
        obj["spec_sha"] = self._get_spectrometer_sha()
        obj["intensity_scalar"] = per_spec.intensity_scalar
        obj["source"] = source
        # save the conditionals
        obj["conditionals"] = (
            [c.to_dict() for c in per_spec.conditionals]
            if per_spec.conditionals
            else None
        )
        obj["tripped_conditional"] = (
            per_spec.tripped_conditional.result_dict()
            if per_spec.tripped_conditional
            else None
        )

        # save the scripts
        ms = per_spec.run_spec.mass_spectrometer
        for si in (
            "measurement",
            "extraction",
            "post_measurement",
            "post_equilibration",
            "hops",
        ):
            name = getattr(per_spec, "{}_name".format(si))
            blob = getattr(per_spec, "{}_blob".format(si))
            if name:
                self.dvc.meta_repo.update_script(ms, name, blob)
            obj[si] = name

        # save keys for the arar isotopes
        akeys = self.arar_mapping
        if akeys is None:
            akeys = ARAR_MAPPING

        obj["arar_mapping"] = akeys

        # save experiment
        self.debug("---------------- Experiment Queue saving disabled")
        # self.dvc.update_experiment_queue(ms, self.per_spec.experiment_queue_name,
        #                                  self.per_spec.experiment_queue_blob)

        self._save_macrochron(obj)

        hexsha = str(self.dvc.get_meta_head())
        obj["meta_commit"] = hexsha
        dchexsha = str(self.dvc.get_version())
        obj["data_collection_commit"] = dchexsha
        # dump runid.json
        p = self._make_path()
        dvc_dump(obj, p)

        p = self._make_path(modifier=INTERCEPTS)
        dvc_dump(intercepts, p)

        # dump runid.blank.json
        p = self._make_path(modifier=BLANKS)
        dvc_dump(blanks, p)

        p = self._make_path(modifier=BASELINES)
        dvc_dump(cbaselines, p)

        p = self._make_path(modifier=ICFACTORS)
        dvc_dump(icfactors, p)

        # dump runid.data.json
        p = self._make_path(modifier=".data")
        data = {
            "data_collection_commit": dchexsha,
            "encoding": "base64",
            "format": "{}ff".format(endianness),
            "signals": signals,
            "baselines": baselines,
            "sniffs": sniffs,
        }
        dvc_dump(data, p)

    def _save_macrochron(self, obj):
        pass

    def _save_monitor(self):
        if self.per_spec.monitor:
            p = self._make_path(modifier="monitor")
            checks = []
            for ci in self.per_spec.monitor.checks:
                data = encode_blob(pack(">ff", ci.data))
                params = dict(
                    name=ci.name,
                    parameter=ci.parameter,
                    criterion=ci.criterion,
                    comparator=ci.comparator,
                    tripped=ci.tripped,
                    data=data,
                )
                checks.append(params)

            dvc_dump(checks, p)

    def _save_spectrometer_file(self, path):
        obj = dict(
            spectrometer=dict(self.per_spec.spec_dict),
            gains=dict(self.per_spec.gains),
            deflections=dict(self.per_spec.defl_dict),
            settings=self.per_spec.settings,
        )
        # hexsha = self.dvc.get_meta_head()
        # obj['commit'] = str(hexsha)

        dvc_dump(obj, path)

    def _save_peak_center(self, pc):
        self.info("DVC saving peakcenter")
        p = self._make_path(modifier="peakcenter")

        if pc:
            fmt = ">ff"
            obj = {
                "reference_detector": pc.reference_detector.name,
                "reference_isotope": pc.reference_isotope,
                "fmt": fmt,
                "interpolation": pc.interpolation_kind if pc.use_interpolation else "",
            }

            results = pc.get_results()
            if results:
                for result in results:
                    points = encode_blob(pack(fmt, result.points))

                    obj[result.detector] = {
                        "low_dac": result.low_dac,
                        "center_dac": result.center_dac,
                        "high_dac": result.high_dac,
                        "low_signal": result.low_signal,
                        "center_signal": result.center_signal,
                        "high_signal": result.high_signal,
                        "resolution": result.resolution,
                        "low_resolving_power": result.low_resolving_power,
                        "high_resolving_power": result.high_resolving_power,
                        "points": points,
                    }

            dvc_dump(obj, p)

    def _make_path(self, modifier=None, extension=".json"):
        runid = self.per_spec.run_spec.runid
        uuid = self.per_spec.run_spec.uuid
        repository_identifier = self.per_spec.run_spec.repository_identifier

        if self.use_uuid_path_name:
            name = uuid, uuid
        else:
            name = runid, runid

        return analysis_path(
            name, repository_identifier, modifier, extension, mode="w", force_sublen=2
        )

    def _make_analysis_dict(self, keys=None):
        if keys is None:
            keys = META_ATTRS

        def get(ki):
            obj = self.per_spec
            if not hasattr(obj, ki):
                obj = self.per_spec.run_spec
            try:
                return getattr(obj, ki)
            except AttributeError as e:
                self.warning("Attribute error: attr={}, error={}".format(ki, e))

        d = {k: get(k) for k in keys}
        return d

    def _get_spectrometer_sha(self):
        """
        return a sha-1 hash.

        generate using spec_dict, defl_dict, and gains
        spec_dict: source parameters, cdd operating voltage
        defl_dict: detector deflections
        gains: detector gains

        make hash using
        for key,value in dictionary:
            sha1.update(key)
            sha1.update(value)

        to ensure consistence, dictionaries are sorted by key
        for key,value in sorted(dictionary)
        :return:
        """
        return spectrometer_sha(
            self.per_spec.settings,
            self.per_spec.spec_dict,
            self.per_spec.defl_dict,
            self.per_spec.gains,
        )

        # ============= EOF =============================================
        #         self._save_measured_positions()
        #
        #
        # def _save_measured_positions(self):
        #     dvc = self.dvc
        #
        #     load_name = self.per_spec.load_name
        #     for i, pp in enumerate(self.per_spec.positions):
        #         if isinstance(pp, tuple):
        #             if len(pp) > 1:
        #                 if len(pp) == 3:
        #                     dvc.add_measured_position('', load_name, x=pp[0], y=pp[1], z=pp[2])
        #                 else:
        #                     dvc.add_measured_position('', load_name, x=pp[0], y=pp[1])
        #             else:
        #                 dvc.add_measured_position(pp[0], load_name)
        #
        #         else:
        #             dbpos = dvc.add_measured_position(pp, load_name)
        #             try:
        #                 ep = self.per_spec.extraction_positions[i]
        #                 dbpos.x = ep[0]
        #                 dbpos.y = ep[1]
        #                 if len(ep) == 3:
        #                     dbpos.z = ep[2]
        #             except IndexError:
        #                 self.debug('no extraction position for {}'.format(pp))
