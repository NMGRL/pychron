# ===============================================================================
# Copyright 2019 ross
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
from random import random

from numpy import array
from pyface.confirmation_dialog import confirm
from pyface.constant import OK, YES
from pyface.file_dialog import FileDialog
from traits.api import (
    Float,
    Int,
    Str,
    HasTraits,
    List,
    Button,
    CFloat,
    CInt,
    on_trait_change,
    Bool,
)
from traitsui.api import (
    UItem,
    TableEditor,
    HGroup,
    Item,
    VGroup,
    ListStrEditor,
    Handler,
    HSplit,
    VSplit,
)
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.menu import Action, Menu as MenuManager
from traitsui.table_column import ObjectColumn
from uncertainties import ufloat

from pychron.core.csv.csv_parser import CSVColumnParser
from pychron.core.fuzzyfinder import fuzzyfinder
from pychron.core.helpers.iterfuncs import groupby_key
from pychron.core.helpers.strtools import to_bool
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.pychron_traits import BorderVGroup
from pychron.core.stats import calculate_weighted_mean, calculate_mswd
from pychron.core.ui.dialogs import cinformation
from pychron.core.ui.strings import SpacelessStr
from pychron.core.ui.table_editor import myTableEditor
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.processing.analyses.file_analysis import FileAnalysis
from pychron.processing.isotope import Isotope
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA

HEADER = "status", "runid", "age", "age_err", "group", "aliquot", "sample", "label_name"
SPECTRUM_HEADER = HEADER + ("k39", "k39_err", "rad40", "rad40_err")
ISOCHRON_HEADER = (
    "status",
    "runid",
    "ar40",
    "ar40_err",
    "ar39",
    "ar39_err",
    "ar36",
    "ar36_err",
    "group",
    "aliquot",
    "sample",
    "label_name",
)
REGRESSION_HEADER = (
    "status",
    "runid",
    "x",
    "x_err",
    "y",
    "y_err",
    "group",
    "aliquot",
    "sample",
    "label_name",
)


def make_line(vs, delimiter=","):
    return "{}\n".format(delimiter.join(vs))


class CSVRecord(HasTraits):
    runid = Str("")
    age = CFloat
    age_err = CFloat

    group = CInt
    aliquot = CInt
    sample = Str
    status = Bool(True)
    label_name = Str
    header = HEADER

    def __init__(self, *args, **kw):
        if "status" in kw:
            kw["status"] = to_bool(kw["status"])
        super(CSVRecord, self).__init__(*args, **kw)

    def valid(self):
        return self.runid and self.age and self.age_err

    def to_csv(self, delimiter=","):
        return make_line(
            [str(getattr(self, attr)) for attr in self.header], delimiter=delimiter
        )


class CSVSpectrumRecord(CSVRecord):
    header = SPECTRUM_HEADER
    k39 = CFloat
    k39_err = CFloat
    rad40 = CFloat
    rad40_err = CFloat


class CSVIsochronRecord(CSVRecord):
    header = ISOCHRON_HEADER

    ar40 = CFloat
    ar40_err = CFloat
    ar39 = CFloat
    ar39_err = CFloat
    ar36 = CFloat
    ar36_err = CFloat

    def valid(self):
        return (
            self.runid
            and self.ar40
            and self.a40_err
            and self.ar39
            and self.ar39_err
            and self.ar36
            and self.ar36_err
        )


class CSVRegressionRecord(CSVRecord):
    header = REGRESSION_HEADER
    x = CFloat
    y = CFloat
    x_err = CFloat
    y_err = CFloat

    def __init__(self, test=False, *args, **kw):
        super(CSVRegressionRecord, self).__init__(*args, **kw)
        if test:
            self.x = test
            self.y = 10 - test + random() / 10
            self.x_err = random()
            self.y_err = random()

    def valid(self):
        return (self.x or self.x_err) and (self.y or self.y_err)


class CSVRecordGroup(HasTraits):
    name = Str
    records = List
    weighted_mean = Float
    mean = Float
    std = Float

    weighted_mean_err = Float
    mswd = Float
    n = Int
    excluded = Int
    displayn = Str
    min = Float
    max = Float
    dev = Float
    percent_dev = Float
    calculate_name = "records:[age,age_err,status]"

    def __init__(self, name, records, *args, **kw):
        super(CSVRecordGroup, self).__init__(*args, **kw)

        self.name = str(name)
        self.records = list(records)
        self.on_trait_change(self.calculate, self.calculate_name)
        self.calculate()

    def calculate(self):
        total = len(self.records)
        if not total:
            return

        data = self._get_data()
        if not data:
            return

        self._calculate(total, data)

    def _get_data(self):
        return [(a.age, a.age_err) for a in self.records if a.status]

    def _calculate(self, total, data):
        data = array(data)
        x, errs = data.T

        self.mean = x.mean()
        self.std = x.std()

        self.n = n = len(x)
        self.weighted_mean, self.weighted_mean_err = calculate_weighted_mean(x, errs)

        self.mean = sum(x) / n
        self.mswd = calculate_mswd(x, errs, wm=self.weighted_mean)

        self.min = min(x)
        self.max = max(x)
        self.dev = self.max - self.min
        try:
            self.percent_dev = self.dev / self.max * 100
        except ZeroDivisionError:
            self.percent_dev = 0

        self.displayn = "{}".format(n)
        if total > n:
            self.displayn = "{}/{}".format(n, total)


class CSVDataSetFactoryHandler(Handler):
    def close(self, info, is_ok):
        if info.object.dirty:
            if (
                not confirm(
                    None, "You have unsaved changes. Are you sure you want to continue"
                )
                == YES
            ):
                return False

        return True


class CSVRegressionRecordGroup(CSVRecordGroup):
    calculate_name = "records:[y,y_err,status]"

    def _get_data(self):
        return [(a.y, a.y_err) for a in self.records if a.status]


class CSVDataSetFactory(Loggable):
    records = List
    groups = List

    selected = List
    add_record_button = Button("Add Row")
    test_button = Button("Load Test Data")
    save_button = Button("Save")
    save_as_button = Button("Save As")
    clear_button = Button("Clear")
    # calculate_button = Button('Calculate')
    open_via_finder_button = Button("Use Finder")
    open_help_button = Button("Help")

    name = SpacelessStr
    names = List
    onames = List

    repository = Str
    repositories = List
    orepositories = List

    data_path = None

    name_filter = Str
    repo_filter = Str
    dirty = False
    _record_klass = CSVRecord
    _group_klass = CSVRecordGroup

    _message_text = """Create/select a file with a column header as the first line.<br/><br/>
        
The following columns are required:<br/>
&nbsp;&nbsp;<b>runid, age, age_err</b><br/><br/>

Optional columns are:<br/>
&nbsp;&nbsp;<b>group, aliquot, sample, label_name, kca, kca_err, radiogenic_yield, radiogenic_yield_err</b><br/><br/>

e.g.
<table cellpadding="3" style="border-width: 1px; border-color: black; border-style: solid;">
<tr>
    <th>runid</th>
    <th>age</th>
    <th>age_err</th>
</tr>
<tr><td>Run1</td><td>10</td><td>0.24</tr>
<tr><td>Run2</td><td>11</td><td>0.13</tr>
<tr><td>Run3</td><td>12</td><td>0.40</tr>

</table>"""

    def as_analyses(self):
        ret = []
        if not self.data_path:
            ret = [FileAnalysis.from_csv_record(ri) for ri in self.records]

        return ret

    def load(self):
        self.repositories = self.dvc.get_local_repositories()
        self.orepositories = self.repositories
        if to_bool(os.getenv("CSV_DEBUG")):
            self.records = [CSVRecord() for i in range(3)]
            self._test_button_fired()

    def dump(self):
        local_path = False
        if not self.repository:
            if YES == confirm(
                None,
                "Would you like to save the file locally?\n"
                "Otherwise please select a repository to save the data "
                "file",
            ):
                dlg = FileDialog(action="save as", default_directory=paths.csv_data_dir)
                if dlg.open():
                    local_path = dlg.path

                if not local_path:
                    return
                else:
                    name, ext = os.path.splitext(os.path.basename(local_path))
                    self.name = name
            else:
                return

        if not self.name:
            self._save_as_button_fired()
        else:
            p = self.dvc.save_csv_dataset(
                self.name, self.repository, self._make_csv_data(), local_path=local_path
            )
            if p:
                self.data_path = p
                self.dirty = False

    # private
    # handlers
    # def _calculate_button_fired(self):
    #     for gi in self.groups:
    #         gi.calculate()

    def _record_factory(self):
        record = self._record_klass()
        return record

    def _add_record_button_fired(self):
        self.records.append(self._record_factory())
        self._make_groups()

    def _name_filter_changed(self, new):
        if new:
            self.names = fuzzyfinder(new, self.onames)
        else:
            self.names = self.onames

    def _repo_filter_changed(self, new):
        if new:
            self.repositories = fuzzyfinder(new, self.orepositories)
        else:
            self.repositories = self.orepositories

    def _name_changed(self):
        p = os.path.join(
            paths.repository_dataset_dir,
            self.repository,
            "csv",
            "{}.csv".format(self.name),
        )
        self._load_csv_data(p)

    def _repository_changed(self, new):
        if new:
            self._load_names(new)

    def _open_help_button_fired(self):
        cinformation(message=self._message_text, title="CSV Format")

    def _open_via_finder_button_fired(self):
        dlg = FileDialog(default_directory=paths.csv_data_dir, action="open")
        if dlg.open() == OK:
            if dlg.path:
                self._load_csv_data(dlg.path)

    def _save_button_fired(self):
        self.dump()

    def _save_as_button_fired(self):
        info = self.edit_traits(okcancel_view(Item("name"), title="New Dataset Name"))
        if info.result:
            self.dump()
            self._load_names()

    def _clear_button_fired(self):
        self.records = self._records_default()
        self._make_groups()

    @on_trait_change("records:[+]")
    def _handle_change(self):
        self.dirty = True
        self._make_groups()

    @on_trait_change("records:group")
    def _handle_group_change(self):
        self._make_groups()

    def _make_groups(self):
        rs = [r for r in self.records if r.valid()]
        self.groups = [
            self._group_klass(gid, rs) for gid, rs in groupby_key(rs, "group")
        ]

    def _load_csv_data(self, p):
        if os.path.isfile(p):
            try:
                parser = CSVColumnParser()
                parser.load(p)

                records = [self._record_klass(**row) for row in parser.values()]
                self.records = records

                self._make_groups()

                self.data_path = p
                self.dirty = False
            except BaseException:
                self.debug_exception()
                self.warning_dialog(
                    "Failed to load csv file '{}'. Please check its format!".format(p)
                )

    def _make_csv_data(self):
        header = self.records[0].header
        return [make_line(header)] + [ri.to_csv() for ri in self.records if ri.valid()]

    def _load_names(self, repo=None):
        if repo is None:
            repo = self.repository

        self.names = self.dvc.get_csv_datasets(repo)
        self.onames = self.names

    def _records_default(self):
        return []

    def _group_selected(self, selection=None):
        if selection:
            gid = max([r.group for r in self.records]) + 1
            for si in selection:
                si.group = gid

    def _get_columns(self):
        cols = [
            CheckboxColumn(name="status"),
            ObjectColumn(name="runid", width=50, label="RunID"),
            ObjectColumn(name="age", width=100),
            ObjectColumn(name="age_err", width=100, label=PLUSMINUS_ONE_SIGMA),
            ObjectColumn(name="group"),
            ObjectColumn(name="aliquot"),
            ObjectColumn(name="sample"),
            ObjectColumn(name="label_name", label="Label Name"),
        ]
        return cols

    def traits_view(self):
        def paste_factory(runid, row):
            if "," in row:
                vs = row.split(",")
            else:
                vs = row.split("\t")

            n = len(vs)
            age, err, group, aliquot, sample, label_name = 0, 0, 0, 0, "", ""
            if n == 2:
                age, err = vs
            elif n == 3:
                runid, age, err = vs
            elif n == 4:
                runid, age, err, group = vs
            elif n == 5:
                runid, age, err, group, aliquot = vs
            elif n == 6:
                runid, age, err, group, aliquot, sample = vs
            elif n == 7:
                runid, age, err, group, aliquot, sample, label_name = vs

            return CSVRecord(
                status=True,
                runid=runid,
                age=age,
                age_err=err,
                group=group,
                aliquot=aliquot,
                sample=sample,
                label_name=label_name,
            )

        cols = self._get_columns()

        gcols = [
            ObjectColumn(name="name"),
            ObjectColumn(
                name="weighted_mean",
                label="Wtd. Mean",
                format="%0.6f",
            ),
            ObjectColumn(
                name="weighted_mean_err", format="%0.6f", label=PLUSMINUS_ONE_SIGMA
            ),
            ObjectColumn(name="mswd", format="%0.3f", label="MSWD"),
            ObjectColumn(name="displayn", label="N"),
            ObjectColumn(name="mean", format="%0.6f", label="Mean"),
            ObjectColumn(name="std", format="%0.6f", label="Std"),
            ObjectColumn(name="min", format="%0.6f", label="Min"),
            ObjectColumn(name="max", format="%0.6f", label="Max"),
            ObjectColumn(name="dev", format="%0.6f", label="Dev."),
            ObjectColumn(name="percent_dev", format="%0.2f", label="% Dev."),
        ]

        button_grp = (
            HGroup(
                icon_button_editor("save_button", "disk", tooltip="Save"),
                icon_button_editor("save_as_button", "save_as", tooltip="Save As"),
                icon_button_editor(
                    "clear_button", "clear", tooltip="Clear current data"
                ),
                icon_button_editor("add_record_button", "add"),
                # icon_button_editor('test_button', 'test'),
                icon_button_editor(
                    "open_help_button",
                    "help",
                    tooltip="Show CSV formatting instructions",
                ),
                UItem(
                    "open_via_finder_button", tooltip="Open a csv file on your computer"
                ),
                # UItem('calculate_button')
            ),
        )

        repo_grp = VGroup(
            BorderVGroup(
                UItem("repo_filter"),
                UItem(
                    "repositories",
                    width=200,
                    editor=ListStrEditor(selected="repository"),
                ),
                label="Repositories",
            ),
            BorderVGroup(
                UItem("name_filter"),
                UItem("names", editor=ListStrEditor(selected="name")),
                label="DataSets",
            ),
        )

        record_grp = VSplit(
            UItem(
                "records",
                editor=myTableEditor(
                    columns=cols,
                    selected="selected",
                    sortable=False,
                    edit_on_first_click=False,
                    paste_factory=paste_factory,
                    # clear_selection_on_dclicked=True,
                    menu=MenuManager(
                        Action(name="Group Selected", perform=self._group_selected)
                    ),
                    selection_mode="rows",
                ),
            ),
            UItem("groups", editor=TableEditor(columns=gcols)),
        )

        main_grp = HSplit(repo_grp, record_grp)

        v = okcancel_view(
            VGroup(button_grp, main_grp),
            width=1100,
            height=500,
            title="CSV Dataset",
            # handler=CSVDataSetFactoryHandler()
        )
        return v

    def _test_button_fired(self):
        self._load_test_data()

    def _load_test_data(self):
        self.records[0].runid = "A"
        self.records[1].runid = "B"
        self.records[2].runid = "C"

        self.records[0].age = 1
        self.records[1].age = 2
        self.records[2].age = 3

        self.records[0].age_err = 0.10
        self.records[1].age_err = 0.20
        self.records[2].age_err = 0.30

        self.records[0].k39 = 10
        self.records[1].k39 = 20
        self.records[2].k39 = 30

        self.records[0].k39_err = 0.100
        self.records[1].k39_err = 0.200
        self.records[2].k39_err = 0.300

        self.records[0].rad40 = 10
        self.records[1].rad40 = 20
        self.records[2].rad40 = 30

        self.records[0].rad40_err = 0.100
        self.records[1].rad40_err = 0.200
        self.records[2].rad40_err = 0.300

        self._make_groups()
        # rs = [r for r in self.records if r.valid()]
        # self.groups = [CSVRecordGroup(gid, rs) for gid, rs in groupby_key(rs, 'group')]


class CSVSpectrumDataSetFactory(CSVDataSetFactory):
    _message_text = """Create/select a file with a column header as the first line.<br/><br/>
        
The following columns are required:<br/>
&nbsp;&nbsp;<b>runid, age, age_err, k39, k39_err, rad40, rad40_err</b><br/><br/>

Optional columns are:<br/>
&nbsp;&nbsp;<b>group, aliquot, sample, label_name, kca, kca_err, radiogenic_yield, radiogenic_yield_err</b><br/><br/>

e.g.
<table cellpadding="3" style="border-width: 1px; border-color: black; border-style: solid;">
<tr>
    <th>runid</th>
    <th>age</th>
    <th>age_err</th>
    <th>k39</th>
    <th>k39_err</th> 
    <th>rad40</th> 
    <th>rad40_err</th>
</tr>
<tr><td>Run1</td><td>10</td><td>0.24</td><td>0.4</td><td>0.001</td><td>1</td><td>0.1</td></tr>
<tr><td>Run2</td><td>11</td><td>0.13</td><td>0.24</td><td>0.004</td><td>1.1</td><td>0.1</td></tr>
<tr><td>Run3</td><td>12</td><td>0.40</td><td>0.44</td><td>0.003</td><td>1.5</td><td>0.1</td></tr>

</table>
"""

    # Run1, 10, 0.24, 0.4, 0.001, 1, 0.1
    # Run2, 11, 0.32, 0.23, 0.02, 2, 0.1
    # Run3, 10, 0.40, 0.01, 0.1, 4, 0.1
    _record_klass = CSVSpectrumRecord

    def _get_columns(self):
        cols = [
            CheckboxColumn(name="status"),
            ObjectColumn(name="runid", width=50, label="RunID"),
            ObjectColumn(name="age", width=100),
            ObjectColumn(name="age_err", width=100, label=PLUSMINUS_ONE_SIGMA),
            ObjectColumn(name="k39", width=100),
            ObjectColumn(name="k39_err", width=100, label=PLUSMINUS_ONE_SIGMA),
            ObjectColumn(name="rad40", width=100),
            ObjectColumn(name="rad40_err", width=100, label=PLUSMINUS_ONE_SIGMA),
            ObjectColumn(name="group"),
            ObjectColumn(name="aliquot"),
            ObjectColumn(name="sample"),
            ObjectColumn(name="label_name", label="Label Name"),
        ]
        return cols


class CSVIsochronDataSetFactory(CSVDataSetFactory):
    _message_text = """Create/select a file with a column header as the first line.<br/><br/>

    The following columns are required:<br/>
    &nbsp;&nbsp;<b>runid, ar40, ar40_err, ar39, ar39_err, ar36, ar36_err</b><br/><br/>

    Optional columns are:<br/>
    &nbsp;&nbsp;<b>group, aliquot, sample, label_name</b><br/><br/>

    e.g.
    <table cellpadding="3" style="border-width: 1px; border-color: black; border-style: solid;">
    <tr>
        <th>runid</th>
        <th>ar40</th>
        <th>ar40_err</th>
        <th>ar39</th>
        <th>ar39_err</th> 
        <th>ar36</th> 
        <th>ar36_err</th>
    </tr>
    <tr><td>Run1</td><td>10</td><td>0.24</td><td>0.4</td><td>0.001</td><td>1</td><td>0.1</td></tr>
    <tr><td>Run2</td><td>11</td><td>0.13</td><td>0.24</td><td>0.004</td><td>1.1</td><td>0.1</td></tr>
    <tr><td>Run3</td><td>12</td><td>0.40</td><td>0.44</td><td>0.003</td><td>1.5</td><td>0.1</td></tr>

    </table>
    """

    # Run1, 10, 0.24, 0.4, 0.001, 1, 0.1
    # Run2, 11, 0.32, 0.23, 0.02, 2, 0.1
    # Run3, 10, 0.40, 0.01, 0.1, 4, 0.1
    _record_klass = CSVIsochronRecord

    def _get_columns(self):
        cols = [
            CheckboxColumn(name="status"),
            ObjectColumn(name="runid", width=50, label="RunID"),
            ObjectColumn(name="ar40", width=100),
            ObjectColumn(name="ar40_err", width=100, label=PLUSMINUS_ONE_SIGMA),
            ObjectColumn(name="ar39", width=100),
            ObjectColumn(name="ar39_err", width=100, label=PLUSMINUS_ONE_SIGMA),
            ObjectColumn(name="ar36", width=100),
            ObjectColumn(name="ar36_err", width=100, label=PLUSMINUS_ONE_SIGMA),
            ObjectColumn(name="group"),
            ObjectColumn(name="aliquot"),
            ObjectColumn(name="sample"),
            ObjectColumn(name="label_name", label="Label Name"),
        ]
        return cols

    def _load_test_data(self):
        r1 = self._record_klass()
        r2 = self._record_klass()
        r3 = self._record_klass()

        r1.runid = "foo-1"
        r2.runid = "foo-2"
        r3.runid = "foo-3"

        r1.ar40 = 10
        r1.ar40_err = 0.1

        r1.ar39 = 10
        r1.ar39_err = 0.1

        r1.ar36 = 1
        r1.ar36_err = 0.01

        r2.ar40 = 10.4
        r2.ar40_err = 0.1

        r2.ar39 = 10.5
        r2.ar39_err = 0.1

        r2.ar36 = 1.1
        r2.ar36_err = 0.01

        r3.ar40 = 11.3
        r3.ar40_err = 0.1

        r3.ar39 = 9.4
        r3.ar39_err = 0.1

        r3.ar36 = 1.4
        r3.ar36_err = 0.01

        self.records = [r1, r2, r3]


class CSVRegressionDataSetFactory(CSVDataSetFactory):
    _message_text = """Create/select a file with a column header as the first line.<br/><br/>

        The following columns are required:<br/>
        &nbsp;&nbsp;<b>runid, x, y</b><br/><br/>

        Optional columns are:<br/>
        &nbsp;&nbsp;<b>x_err, y_err, group, aliquot, sample, label_name</b><br/><br/>

        e.g.
        <table cellpadding="3" style="border-width: 1px; border-color: black; border-style: solid;">
        <tr>
            <th>runid</th>
            <th>x</th>
            <th>x_err</th>
            <th>y</th>
            <th>y_err</th> 
        </tr>
        <tr><td>Run1</td><td>10</td><td>0.24</td><td>0.4</td><td>0.001</td><td>1</td><td>0.1</td></tr>
        <tr><td>Run2</td><td>11</td><td>0.13</td><td>0.24</td><td>0.004</td><td>1.1</td><td>0.1</td></tr>
        <tr><td>Run3</td><td>12</td><td>0.40</td><td>0.44</td><td>0.003</td><td>1.5</td><td>0.1</td></tr>

        </table>
    """
    _record_klass = CSVRegressionRecord
    _group_klass = CSVRegressionRecordGroup

    def _record_factory(self):
        record = self._record_klass(test=len(self.records) + 1)
        return record

    def _get_columns(self):
        cols = [
            CheckboxColumn(name="status"),
            ObjectColumn(name="runid", width=50, label="RunID"),
            ObjectColumn(name="x", width=100),
            ObjectColumn(name="x_err", width=100, label=PLUSMINUS_ONE_SIGMA),
            ObjectColumn(name="y", width=100),
            ObjectColumn(name="y_err", width=100, label=PLUSMINUS_ONE_SIGMA),
            ObjectColumn(name="group"),
            ObjectColumn(name="aliquot"),
            ObjectColumn(name="sample"),
            ObjectColumn(name="label_name", label="Label Name"),
        ]
        return cols

    def _load_test_data(self):
        self.records = [
            self._record_klass(runid="foo-{}".format(i), test=i + 1) for i in range(10)
        ]


if __name__ == "__main__":

    class DVC:
        def save_csv_dataset(self, name, repo, lines):
            p = "csv_dataset_test.csv"
            with open(p, "w") as wfile:
                wfile.writelines(lines)

        def get_local_repositories(self):
            return ["a", "b", "c"]

        def get_csv_datasets(self, repo):
            return ["1", "2", "3", repo]

    c = CSVDataSetFactory()
    c.dvc = DVC()
    c.load()

    # c.records[0].runid = 'A'
    # c.records[1].runid = 'B'
    # c.records[2].runid = 'C'
    #
    # c.records[0].age = 1
    # c.records[1].age = 2
    # c.records[2].age = 3
    #
    # c.records[0].age_err = 10
    # c.records[1].age_err = 20
    # c.records[2].age_err = 30
    c.configure_traits()
# ============= EOF =============================================
