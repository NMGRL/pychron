# ===============================================================================
# Copyright 2014 Jake Ross
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
from __future__ import absolute_import
from __future__ import print_function

import os

import six
from traits.api import HasTraits, Button, String, List, Any, Instance
from traitsui.api import (
    View,
    UItem,
    HGroup,
    VGroup,
    ListStrEditor,
    HSplit,
    TabularEditor,
)

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import glob_list_directory, add_extension
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.experiment.automated_run.spec import AutomatedRunSpec
from pychron.experiment.automated_run.tabular_adapter import RunBlockAdapter
from pychron.experiment.automated_run.uv.spec import UVAutomatedRunSpec
from pychron.experiment.queue.parser import RunParser, UVRunParser
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.pychron_constants import FUSIONS_UV


class RunBlock(Loggable):
    extract_device = String
    mass_spectrometer = String
    repository_identifier = String

    def _add_queue_meta(self, params):
        pass

    def make_runs(self, path):
        with open(path, "r") as rfile:
            line_gen = self._get_line_generator(rfile)
            return self._load_runs(line_gen)

    def _get_line_generator(self, txt):
        if isinstance(txt, (str, six.text_type)):
            return (l for l in txt.split("\n"))
        else:
            return txt

    def _runs_gen(self, line_gen):
        delim = "\t"

        lines = list(line_gen)

        header = [l.strip() for l in lines[0].split(delim)]
        pklass = RunParser
        if self.extract_device == FUSIONS_UV:
            pklass = UVRunParser
        parser = pklass()
        # trim off header
        lines = lines[1:]
        for linenum, line in enumerate(lines):
            # self.debug('loading line {}'.format(linenum))
            skip = False
            line = line.rstrip()

            # load commented runs but flag as skipped
            if line.startswith("##"):
                continue
            if line.startswith("#"):
                skip = True
                line = line[1:]

            if not line:
                continue

            try:
                script_info, params = parser.parse(header, line)
                self._add_queue_meta(params)
                params["skip"] = skip
                params["mass_spectrometer"] = self.mass_spectrometer
                if not params.get("repository_identifier"):
                    params["repository_identifier"] = self.repository_identifier

                klass = AutomatedRunSpec
                if self.extract_device == FUSIONS_UV:
                    klass = UVAutomatedRunSpec

                # get the next runs position and save it to the current run.
                # this allows the current run to move to the next run's position
                try:
                    nextline = lines[linenum + 1]
                except IndexError:
                    nextline = None

                next_params = None
                if nextline:
                    _, next_params = parser.parse(header, nextline)
                # self.debug(f"next line {nextline}")
                # self.debug(f'next_params {next_params}')
                arun = klass()
                arun.load(script_info, params, next_params)

                yield arun

            except Exception as e:
                import traceback

                print(traceback.print_exc())
                self.warning_dialog(
                    "Invalid Experiment file {}\nlinenum= {}\nline= {}".format(
                        e, linenum, line
                    )
                )

                break

    def _load_runs(self, line_gen):
        self.debug("loading runs")
        aruns = list(self._runs_gen(line_gen))
        self.debug("returning nruns {}".format(len(aruns)))
        return aruns


class RunBlockEditView(HasTraits):
    blocks = List
    selected = Any
    block = Instance(RunBlock, ())
    runs = List
    delete_run = Button

    def __init__(self, *args, **kw):
        super(RunBlockEditView, self).__init__(*args, **kw)
        self._load_blocks()

    def _load_blocks(self):
        p = paths.run_block_dir
        blocks = glob_list_directory(p, ".txt", remove_extension=True)
        self.blocks = blocks

    def _delete_run_fired(self):
        if self.selected:
            p = os.path.join(paths.run_block_dir, add_extension(self.selected))
            os.remove(p)
            self._load_blocks()

    def _selected_changed(self, new):
        if new:
            new = add_extension(new)
            runs = self.block.make_runs(os.path.join(paths.run_block_dir, new))
            self.runs = runs

    def traits_view(self):
        adapter = RunBlockAdapter()
        v = View(
            HSplit(
                VGroup(
                    UItem(
                        "blocks", width=0.25, editor=ListStrEditor(selected="selected")
                    ),
                    HGroup(icon_button_editor("delete_run", "delete")),
                ),
                UItem(
                    "runs",
                    width=0.75,
                    editor=TabularEditor(editable=False, adapter=adapter),
                ),
            ),
            width=900,
            resizable=True,
        )
        return v


# ============= EOF =============================================
