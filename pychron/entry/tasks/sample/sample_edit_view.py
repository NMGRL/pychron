# ===============================================================================
# Copyright 2016 ross
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
import re

import pyproj as pyproj
from traits.api import (
    HasTraits,
    Instance,
    List,
    Str,
    Long,
    Float,
    BaseFloat,
    Enum,
    Int,
    CStr,
)
from traits.trait_errors import TraitError
from traitsui.api import View, UItem, Item, VGroup, EnumEditor, HGroup
from traitsui.menu import Action

EN = re.compile(r"(?P<a>[\w\W]+) \((?P<b>[\w\W]+, ?[\w\W]+)\)")

SAMPLE_ATTRS = (
    "lat",
    "lon",
    "igsn",
    "storage_location",
    "lithology",
    "location",
    "approximate_age",
    "elevation",
    "note",
)


class LatFloat(BaseFloat):
    def validate(self, obj, name, value):
        if not isinstance(value, (float, int)):
            return self.error(obj, name, value)
        else:
            if value > 90 or value < -90:
                return self.error(obj, name, value)
            else:
                return value


class LonFloat(BaseFloat):
    def validate(self, obj, name, value):
        if not isinstance(value, (float, int)):
            return self.error(obj, name, value)
        else:
            if value > 180 or value < -180:
                return self.error(obj, name, value)
            else:
                return value


def extract_names(s):
    a = s
    b = None
    mat = EN.match(s)
    if mat:
        a = mat.group("a")
        b = mat.group("b")

    return a, b


class SaveAction(Action):
    name = "Save"
    action = "save"


class SampleEditItem(HasTraits):
    name = Str
    project = Str
    material = Str
    grainsize = Str
    id = Long
    note = Str

    location_mode = Enum("Lat/Lon", "UTM")
    northing = Int
    easting = Int
    utm_zone = Int

    lat = LatFloat
    lon = LonFloat
    igsn = Str
    lithology = CStr
    location = Str
    storage_location = Str
    approximate_age = Float
    elevation = Float

    _projects = List
    _materials = List

    _project = Str
    _material = Str
    _grainsize = CStr
    _note = CStr
    _lat = LatFloat
    _lon = LonFloat
    _igsn = CStr
    _lithology = CStr
    _location = CStr
    _storage_location = CStr
    _approximate_age = Float
    _elevation = Float

    def __init__(self, rec=None, *args, **kw):
        super(SampleEditItem, self).__init__(*args, **kw)
        if rec:
            self.id = rec.id

            self.name = self._name = rec.name
            # self.note = self._note = rec.note or ''

            self.project = self._project = rec.project.pname if rec.project else ""
            self.material = self._material = rec.material.name if rec.material else ""
            self.grainsize = self._grainsize = (
                (rec.material.grainsize or "") if rec.material else ""
            )
            self._easting = 0
            self._northing = 0
            self._utm_zone = 0
            # self.project_name = rec.project.name
            # self.principal_investigator = rec.project.principal_investigator
            for attr in SAMPLE_ATTRS:
                v = getattr(rec, attr)
                if v is not None:
                    try:
                        setattr(self, attr, v)
                        setattr(self, "_{}".format(attr), v)
                    except (TraitError, ValueError) as e:
                        print("unable to set attribute", attr, v, e)
                        pass

    @property
    def altered(self):
        attrs = (
            "name",
            "project",
            "material",
            "grainsize",
            "easting",
            "northing",
            "utm_zone",
        ) + SAMPLE_ATTRS
        try:
            return any(
                (
                    getattr(self, attr) != getattr(self, "_{}".format(attr))
                    for attr in attrs
                )
            )
        except AttributeError:
            return False

    @property
    def project_pi(self):
        proj, pi = extract_names(self.project)
        return proj, pi

    def traits_view(self):
        ll_grp = HGroup(
            Item("lat", label="Latitude"),
            Item("lon", label="Longitude"),
            visible_when='location_mode!="UTM"',
        )
        utm_grp = HGroup(
            Item("easting"),
            Item("northing"),
            Item("utm_zone"),
            visible_when='location_mode=="UTM"',
        )

        vv = View(
            VGroup(
                Item("name", label="Sample Name"),
                Item("project", editor=EnumEditor(name="_projects")),
                Item("material", editor=EnumEditor(name="_materials")),
                Item("grainsize"),
                HGroup(
                    VGroup(
                        UItem("location_mode"),
                        ll_grp,
                        utm_grp,
                        Item("location"),
                        Item("elevation"),
                        label="Location",
                        show_border=True,
                    ),
                    VGroup(
                        Item("lithology"),
                        Item("approximate_age", label="Approx. Age (Ma)"),
                        Item("storage_location"),
                        show_border=True,
                    ),
                ),
                VGroup(UItem("note", style="custom"), show_border=True, label="Note"),
            )
        )
        return vv


class SampleEditModel(HasTraits):
    dvc = Instance("pychron.dvc.dvc.DVC")
    sample = Str
    samples = List
    sample_records = List
    _materials = List
    _projects = List
    sample_item = Instance(SampleEditItem, ())

    def set_sample(self, rec):
        nm = SampleEditItem(rec, _projects=self._projects, _materials=self._materials)
        if self.sample_item:
            for attr in ("location_mode", "utm_zone"):
                setattr(nm, attr, getattr(self.sample_item, attr))

        self.sample_item = nm

    def init(self):
        self._projects = self.dvc.get_project_pnames()
        self._materials = self.dvc.get_material_names()
        self._projections = {}

    def save(self):
        db = self.dvc
        # for si in self.samples:
        si = self.sample_item
        if si.altered:
            dbsam = db.get_sample_id(si.id)
            dbsam.name = si.name
            # dbsam.note = si.note
            # dbsam.lat = si.lat

            for attr in SAMPLE_ATTRS:
                if si.location_mode == "UTM" and attr in ("lat", "lon"):
                    continue
                v = getattr(si, attr)
                setattr(dbsam, attr, v)

            if si.location_mode == "UTM":
                zone = si.utm_zone
                if zone in self._projections:
                    p = self._projections[zone]
                else:
                    p = pyproj.Proj(proj="utm", zone=int(zone), ellps="WGS84")
                    self._projections[zone] = p

                lon, lat = p(si.easting, si.northing, inverse=True)
                dbsam.lat = lat
                dbsam.lon = lon

            dbproj = db.get_project(*si.project_pi)
            if dbproj:
                dbsam.projectID = dbproj.id

            dbmat = db.get_material(si.material, si.grainsize)
            if dbmat:
                dbsam.materialID = dbmat.id

            db.commit()
            db.expire(dbsam)

            return True

    # handlers
    def _sample_changed(self):
        # sams = []
        if len(self.sample) > 2:
            sams = self.dvc.get_samples_by_name(self.sample)
            # sams = [SampleEditItem(si, _projects=self._projects,
            #                        _materials=self._materials) for si in sams]
            self.sample_item = SampleEditItem(
                sams[0], _projects=self._projects, _materials=self._materials
            )
        # self.samples = sams

    def traits_view(self):
        return View(UItem("sample_item", style="custom"))


# ============= EOF =============================================
