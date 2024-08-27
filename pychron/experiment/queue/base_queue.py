# ===============================================================================
# Copyright 2012 Jake Ross
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

import datetime
import os

# ============= standard library imports ========================
# ============= enthought library imports =======================
from traits.api import (
    Instance,
    Str,
    Property,
    Event,
    Bool,
    String,
    List,
    CInt,
    on_trait_change,
)

from pychron.core.helpers.ctx_managers import no_update

# ============= local library imports  ==========================
from pychron.core.yaml import yload
from pychron.experiment.queue.run_block import RunBlock
from pychron.experiment.stats import ExperimentStats
from pychron.experiment.utilities.frequency_generator import frequency_index_gen
from pychron.pychron_constants import (
    NULL_STR,
    LINE_STR,
    FUSIONS_UV,
    COLLECTION_TIME_ZERO_OFFSET,
    USE_CDD_WARMING,
    REPOSITORY_IDENTIFIER,
    DELAY_AFTER,
    COMMENT,
    WEIGHT,
    RAMP_DURATION,
    LIGHT_VALUE,
    PATTERN,
    BEAM_DIAMETER,
    OVERLAP,
    PRECLEANUP,
    POSTCLEANUP,
    CLEANUP,
    DURATION,
    EXTRACT_UNITS,
    EXTRACT_VALUE,
    POSITION,
    SAMPLE,
    CRYO_TEMP, MASS_SPECTROMETER,
)


def extract_meta(line_gen):
    metastr = ""
    # read until break
    for line in line_gen:
        if line.startswith("#====="):
            break
        metastr += "{}\n".format(line)

    return yload(metastr), metastr


METASTR = """
username: {username:}
use_email: {use_email:}
email: {email:}
use_group_email: {use_group_email:}
date: {date:}
queue_conditionals_name: {queue_conditionals:}
delay_before_analyses: {delay_before_analyses:}
delay_between_analyses: {delay_between_analyses:}
delay_after_blank: {delay_after_blank:}
delay_after_air: {delay_after_air:}
delay_after_conditional: {delay_after_conditional:}
extract_device: {extract_device:}
default_lighting: {default_lighting:}
tray: {tray:}
load: {load:}
note: {note:}
"""


class BaseExperimentQueue(RunBlock):
    selected = List

    automated_runs = List
    cleaned_automated_runs = Property  # (depends_on='automated_runs[]')

    username = String
    email = String
    use_group_email = Bool
    use_email = Bool

    note = Str
    tray = Str

    delay_before_analyses = CInt(5)
    delay_between_analyses = CInt(30)
    delay_after_blank = CInt(15)
    delay_after_air = CInt(10)
    delay_after_conditional = Str

    default_lighting = CInt(0)

    queue_conditionals_name = Str

    stats = Instance(ExperimentStats, ())

    # update_needed = Event
    refresh_table_needed = Event
    refresh_info_needed = Event
    changed = Event
    name = Property(depends_on="path")
    path = String

    executable = Bool
    initialized = True

    load_name = Str
    repository_identifier = Str

    _no_update = False
    _frequency_group_counter = 0

    @property
    def no_update(self):
        return self._no_update

    # ===============================================================================
    # persistence
    # ===============================================================================
    def load(self, txt):
        self.initialized = False

        line_gen = self._get_line_generator(txt)
        self._extract_meta(line_gen)

        self.stats.delay_between_analyses = self.delay_between_analyses
        self.stats.delay_before_analyses = self.delay_before_analyses
        self.stats.delay_after_blank = self.delay_after_blank
        self.stats.delay_after_air = self.delay_after_air

        aruns = self._load_runs(line_gen)
        if aruns is not None:
            # set frequency_added_counter
            if aruns:
                self._frequency_group_counter = max(
                    [ri.frequency_group for ri in aruns]
                )

            with no_update(self):
                self.automated_runs = aruns
            self.initialized = True
            self.debug("loading queue successful")
            return True

    def dump(self, stream, runs=None, include_meta=True):
        header, attrs = self._get_dump_attrs()
        writeline = lambda m: stream.write(m + "\n")
        if include_meta:
            # write metadata
            self._meta_dumper(stream)
            writeline("#" + "=" * 80)

        def tab(l, comment=False):
            s = "\t".join([str(li) for li in l])
            if comment:
                s = "#{}".format(s)
            writeline(s)

        tab(header)

        def is_not_null(vi):
            if vi and vi != NULL_STR:
                try:
                    vi = float(vi)
                    return abs(vi) > 1e-15
                except (ValueError, TypeError):
                    return True
            else:
                return False

        if runs is None:
            runs = self.automated_runs

        for arun in runs:
            vs = arun.to_string_attrs(attrs)
            vals = [v if is_not_null(v) else "" for v in vs]
            tab(vals, comment=arun.skip)

        return stream

    def set_extract_device(self, v):
        self.extract_device = v
        for a in self.automated_runs:
            a.extract_device = v

    def is_updateable(self):
        return not self._no_update

    def clear_frequency_runs(self):
        if self._frequency_group_counter:
            self.automated_runs = [
                ri
                for ri in self.automated_runs
                if not ri.frequency_group == self._frequency_group_counter
            ]
            self._frequency_group_counter -= 1

    def extend_runs(self, runs):
        self.automated_runs.extend(runs)
        self.refresh_table_needed = True

    def add_runs(
        self,
        runspecs,
        freq=None,
        freq_before=True,
        freq_after=False,
        is_run_block=False,
        is_repeat_block=False,
    ):
        """
        runspecs: list of runs
        freq: optional inter
        freq_before_or_after: if true add before else add after
        """
        if not runspecs:
            return []

        with no_update(self):
            if freq:
                runs = self._add_frequency_runs(
                    runspecs,
                    freq,
                    freq_before,
                    freq_after,
                    is_run_block,
                    is_repeat_block,
                )
            else:
                runs = self._add_runs(runspecs)

            return runs

    def remove(self, run):
        try:
            self.automated_runs.remove(run)
        except ValueError:
            self.debug("failed to remove {}. not in automated_runs list".format(run))

    def _add_frequency_runs(
        self, runspecs, freq, freq_before, freq_after, is_run_block, is_repeat_block
    ):
        aruns = self.automated_runs
        runblock = self.automated_runs
        if is_repeat_block:
            idx = aruns.index(self.selected[-1])
            sidx = idx + freq
        else:
            if len(self.selected) > 1:
                runblock = self.selected
                sidx = aruns.index(runblock[0])
            else:
                sidx = 0

        self._frequency_group_counter += 1
        fcnt = self._frequency_group_counter

        runs = []
        if is_run_block:
            incrementable_types = ("unknown",)
        else:
            run = runspecs[0]
            rtype = run.analysis_type
            incrementable_types = ("unknown",)

            if len(runspecs) == 1:
                if rtype.startswith("blank"):
                    t = "_".join(rtype.split("_")[1:])
                    incrementable_types = (t,)

        for idx in reversed(
            list(
                frequency_index_gen(
                    runblock,
                    freq,
                    incrementable_types,
                    freq_before,
                    freq_after,
                    sidx=sidx,
                )
            )
        ):
            for ri in reversed(runspecs):
                run = ri.clone_traits()
                run.frequency_group = fcnt
                runs.append(run)
                aruns.insert(idx, run)

        return runs

    def _add_runs(self, runspecs):
        aruns = self.automated_runs

        if self.selected and self.selected[-1] in aruns:
            idx = aruns.index(self.selected[-1])
            for ri in reversed(runspecs):
                if not ri.repository_identifier:
                    ri.repository_identifier = self.repository_identifier

                aruns.insert(idx + 1, ri)
        else:
            aruns.extend(runspecs)
        return runspecs

    def _add_queue_meta(self, params):
        for attr in (
            "extract_device",
            "tray",
            "username",
            "default_lighting",
            # 'email',
            # 'use_group_email',
            "queue_conditionals_name",
        ):
            params[attr] = getattr(self, attr)

    def _extract_meta(self, f):
        meta, metastr = extract_meta(f)

        if meta is None:
            self.warning_dialog(
                "Invalid experiment set file. Poorly formatted metadata {}".format(
                    metastr
                )
            )
            return
        self._load_meta(meta)
        return meta

    def _load_meta(self, meta):
        # default = lambda x: str(x) if x else ' '
        default_int_zero = lambda x: x if x is not None else 0
        default_int = lambda x: x if x is not None else 1
        key_default = lambda k: lambda x: str(x) if x else k
        bool_default = lambda x: bool(x) if x else False
        default = key_default("")

        self._set_meta_param("note", meta, default)
        self._set_meta_param("tray", meta, default)
        self._set_meta_param("extract_device", meta, key_default("Extract Device"))
        # self._set_meta_param("mass_spectrometer", meta, key_default("Spectrometer"))
        self._set_meta_param("delay_between_analyses", meta, default_int)
        self._set_meta_param("delay_before_analyses", meta, default_int)
        self._set_meta_param("delay_after_blank", meta, default_int)
        self._set_meta_param("delay_after_air", meta, default_int)
        self._set_meta_param("delay_after_conditional", meta, default)
        self._set_meta_param("username", meta, default)
        self._set_meta_param("use_email", meta, bool_default)
        self._set_meta_param("email", meta, default)
        self._set_meta_param("use_group_email", meta, bool_default)
        self._set_meta_param("load_name", meta, default, metaname="load")
        self._set_meta_param("queue_conditionals_name", meta, default)
        self._set_meta_param("repository_identifier", meta, default)
        self._set_meta_param("default_lighting", meta, default_int_zero)

        # # load sample map
        # self._load_map()

        self._load_meta_hook(meta)

    def _load_meta_hook(self, meta):
        pass

    # def _load_map(self):
    #     name = self.tray
    #
    #     if name:
    #         name = str(name)
    #         if not name.endswith('.txt'):
    #             name = '{}.txt'.format(name)
    #
    #         name = os.path.join(paths.map_dir, name)
    #         if os.path.isfile(name):
    #             from pychron.stage.maps.laser_stage_map import LaserStageMap
    #             from pychron.experiment.map_view import MapView
    #
    #             sm = LaserStageMap(file_path=name)
    #             mv = MapView(stage_map=sm)
    #             self.map_view = mv

    def _set_meta_param(self, attr, meta, func, metaname=None):
        if metaname is None:
            metaname = attr

        v = None
        try:
            v = meta[metaname]
        except KeyError:
            pass
        v = func(v)

        self.debug("setting {} to {}".format(attr, v))
        setattr(self, attr, v)

    def _get_dump_attrs(self):
        seq = [
            "labnumber",
            SAMPLE,
            POSITION,
            ("e_value", EXTRACT_VALUE),
            ("e_units", EXTRACT_UNITS),
            DURATION,
            CLEANUP,
            PRECLEANUP,
            POSTCLEANUP,
            CRYO_TEMP,
            OVERLAP,
            ("beam_diam", BEAM_DIAMETER),
            PATTERN,
            LIGHT_VALUE,
            ("extraction", "extraction_script"),
            ("ramp", RAMP_DURATION),
            ("t_o", COLLECTION_TIME_ZERO_OFFSET),
            ("measurement", "measurement_script"),
            ("conditionals", "conditionals"),
            ("syn_extraction", "syn_extraction_script"),
            USE_CDD_WARMING,
            ("post_meas", "post_measurement_script"),
            ("post_eq", "post_equilibration_script"),
            ("s_opt", "script_options"),
            ("dis_btw_pos", "disable_between_positons"),
            WEIGHT,
            COMMENT,
            "autocenter",
            "frequency_group",
            REPOSITORY_IDENTIFIER,
            DELAY_AFTER,
            ('spec', MASS_SPECTROMETER),
        ]

        if self.extract_device == FUSIONS_UV:
            seq.extend(("reprate", "mask", "attenuator", "image"))

        seq = [(v, v) if not isinstance(v, tuple) else v for v in seq]
        header, attrs = list(zip(*seq))
        return header, attrs

    def _meta_dumper(self, wfile):
        # ms = self.mass_spectrometer
        # if ms in ("Spectrometer", LINE_STR):
        #     ms = ""

        s = METASTR.format(
            username=self.username,
            use_email=self.use_email,
            email=self.email,
            use_group_email=self.use_group_email,
            date=datetime.datetime.today(),
            queue_conditionals=self.queue_conditionals_name,
            # mass_spectrometer=ms,
            delay_before_analyses=self.delay_before_analyses,
            delay_between_analyses=self.delay_between_analyses,
            delay_after_blank=self.delay_after_blank,
            delay_after_air=self.delay_after_air,
            delay_after_conditional=self.delay_after_conditional,
            extract_device=self.extract_device,
            default_lighting=self.default_lighting,
            tray=self.tray or "",
            load=self.load_name or "",
            note=self.note,
        )

        if wfile:
            wfile.write(s)
        else:
            return s

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _delay_between_analyses_changed(self, new):
        self.stats.delay_between_analyses = new

    def _delay_before_analyses_changed(self, new):
        self.stats.delay_before_analyses = new

    # def _mass_spectrometer_changed(self):
        # ms = self.mass_spectrometer
        # for ai in self.automated_runs:
        #     ai.mass_spectrometer = ms

    # @on_trait_change("automated_runs[]")
    # def _handle_automated_runs(self):
    #     sm = self.application.get_service(
    #         "pychron.spectrometer.base_spectrometer_manager.BaseSpectrometerManager",
    #         query=f"name=='{self.mass_spectrometer}'",
    #     )
    #
    #
    #     for a in self.automated_runs:
    #         a.spectrometer_manager = sm

    # ===============================================================================
    # property get/set
    # ===============================================================================
    def _get_cleaned_automated_runs(self):
        return [
            ci for ci in self.automated_runs if not ci.skip and ci.state == "not run"
        ]

    def _get_name(self):
        if self.path:
            return os.path.splitext(os.path.basename(self.path))[0]
        else:
            return ""

    @property
    def load_holder(self):
        return self.tray


# ============= EOF =============================================
