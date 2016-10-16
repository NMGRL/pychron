# ===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
import os
from cStringIO import StringIO
from datetime import datetime

import pytz
import requests
from lxml import etree
from traits.api import HasTraits, Str, Float, Enum, Property, Date, Time
from traitsui.api import View, VGroup, Item, EnumEditor, Tabbed, UItem, HGroup

from pychron.core.ui.preference_binding import bind_preference
from pychron.igsn.definitions import SAMPLE_ATTRS, SAMPLE_TYPES, ROCK_TYPES, SUB_ROCK_TYPES, ROCK_TYPE_DETAILS, LAT_TT, \
    ELEVATION_TT, LONG_TT
from pychron.loggable import Loggable


class IGSNSampleModel(HasTraits):
    user_code = Str

    sample_type = Enum(SAMPLE_TYPES)
    name = Str
    material = Str
    description = Str
    age_min = Float
    age_max = Float
    age_unit = Str
    collection_method = Str
    latitude = Str
    longitude = Str
    elevation = Str
    primary_location_name = Str
    country = Str
    province = Str
    county = Str
    collector = Str

    _collection_start_date = Date
    _collection_start_time = Time

    collection_date_precision = Enum('year', 'month', 'day', 'time')
    original_archive = Str

    # classification
    rock_type = Enum(ROCK_TYPES)  # 'Igneous'
    sub_rock_type = Str  # 'Plutonic'
    rock_type_detail = Str

    sub_rock_types = Property(depends_on='rock_type')
    rock_type_details = Property(depends_on='rock_type')

    timezone = Enum(pytz.common_timezones)

    def __init__(self, *args, **kw):
        super(IGSNSampleModel, self).__init__(*args, **kw)

        dt = datetime.now()
        self._collection_start_date = dt.date()
        self._collection_start_time = dt.time()
        self.timezone = 'US/Mountain'

    @property
    def collection_start_date(self):
        dt = datetime.combine(self._collection_start_date, self._collection_start_time)
        local = pytz.timezone(self.timezone)
        local_dt = local.localize(dt)
        utc_dt = local_dt.astimezone(pytz.utc)

        # YYYY - MM - DDTHH:MM:SSZ
        return utc_dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    def _get_rock_type_details(self):
        v = []
        if self.rock_type:
            v = ROCK_TYPE_DETAILS[self.rock_type]
        return v

    def _get_sub_rock_types(self):
        v = []
        if self.rock_type:
            v = SUB_ROCK_TYPES[self.rock_type]
        return v

    def traits_view(self):
        required_grp = VGroup(Item('sample_type', label='Sample Type'),
                              Item('name', label='Name'),
                              Item('material', label='Material'),
                              label='Required', show_border=True)

        collection_grp = VGroup(Item('collector', label='Collection'),
                                Item('collection_method', label='Collection Method'),
                                HGroup(Item('_collection_start_date', label='Collection Start Date'),
                                       UItem('_collection_start_time'),
                                       UItem('timezone')),
                                label='Collection')
        location_grp = VGroup(Item('latitude', label='Latitude', tooltip=LAT_TT),
                              Item('longitude', label='Longitude', tooltip=LONG_TT),
                              Item('elevation', label='Elevation', tooltip=ELEVATION_TT),
                              Item('primary_location_name', label='Primary Location Name'),
                              Item('country', label='Country'),
                              Item('province', label='State/Province'),
                              Item('county', label='County'),
                              label='Location')

        age_grp = VGroup(Item('age_min', label='Age Min'),
                         Item('age_max', label='Age Max'),
                         Item('age_unit', label='Age Units'),
                         label='Age')

        optional_grp = VGroup(VGroup(UItem('description', style='custom', height=-100),
                                     label='Description', show_border=True),
                              Item('original_archive', label='Original Archive'),
                              Tabbed(collection_grp, location_grp, age_grp),
                              show_border=True, label='Optional')

        classification_grp = VGroup(Item('rock_type', label='Rock Type'),
                                    Item('sub_rock_type',
                                         enabled_when='sub_rock_types',
                                         editor=EnumEditor(name='sub_rock_types'),
                                         label='Sub Rock Type'),
                                    Item('rock_type_detail',
                                         enabled_when='rock_type_details',
                                         label='Rock Type Detail',
                                         editor=EnumEditor(name='rock_type_details')),
                                    show_border=True, label='Classification')

        v = View(VGroup(Item('user_code', label='SESAR User Code', style='readonly'),
                        required_grp, classification_grp, optional_grp),
                 title='New IGSN',
                 resizable=True,
                 buttons=['OK', 'Cancel'])
        return v


class IGSNService(Loggable):
    # uri = 'https://app.geosamples.org/webservices/upload.php'
    url = 'https://sesardev.geosamples.org/webservices/upload.php'
    username = Str
    password = Str
    usercode = Str

    def __init__(self, bind=True, *args, **kw):
        super(IGSNService, self).__init__(*args, **kw)
        if bind:
            self._bind_preferences()

    def get_new_igsn(self, sample, material):

        model = IGSNSampleModel(name=sample, material=material,
                                usercode=self.usercode,
                                sample_type='Individual Sample')
        info = model.edit_traits(kind='livemodal')
        if not info.result:
            return

        content = self._assemble_content(model)
        # print content
        print self.username, self.password
        r = requests.post(self.url,
                          data={'content': content,
                                'username': self.username,
                                'password': self.password})

        igsn = self._parse_response(r, single=True)
        return igsn

    def _parse_response(self, r, single=False):
        # status_code = 200
        # text = '<results><valid code="InvalidAuth">no</valid><error>Please enter your username and password.</error></results>'
        # text = '<results> <sample> <status>Sample [Lulin Upload Status Sample test] was saved successfully with IGSN ' \
        #        '[LLS00009I].</status> <name>Lulin Upload Status Sample test</name> <igsn>LLS00009I' \
        #        '</igsn> </sample> </results>'

        text = r.text
        status_code = r.status_code

        tree = etree.parse(StringIO(text))
        igsns = None

        if status_code == 200:
            samples = tree.findall('sample')
            if not samples:
                self.warning_dialog('No results returned. Contact developer')
            else:
                for sample in samples:
                    igsn = sample.find('igsn')
                    igsns.append(igsn.text)

                if single:
                    igsns = igsns[0]
        else:
            error = tree.find('error')
            self.warning_dialog('Failed Getting a new IGSN.\nError={}'.format(error.text))

        return igsns

    def _assemble_content(self, samples):
        if not isinstance(samples, (tuple, list)):
            samples = (samples,)

        root = etree.Element('samples')
        for si in samples:
            self._add_sample(root, si)
        return etree.tostring(root, pretty_print=True)

    def _add_sample(self, root, si):
        se = etree.SubElement(root, 'sample')
        self._add_classification(se, si)

        for tag, iattr, required in SAMPLE_ATTRS:
            if tag == 'user_code':
                val = self.usercode
            else:
                val = self._get_value(si, tag, iattr, required)

            if val:
                elem = etree.SubElement(se, tag)
                elem.text = self._get_value(si, tag, iattr, required)

    def _add_classification(self, se, si):
        clf = etree.SubElement(se, 'classification')
        rock = etree.SubElement(clf, 'Rock')

        elem = etree.SubElement(rock, si.rock_type)
        type_tag = '{}Type'.format(si.rock_type)
        if si.sub_rock_type:
            elem = etree.SubElement(elem, si.sub_rock_type)
            type_tag = '{}Type'.format(si.sub_rock_type)

        if si.rock_type_detail:
            elem = etree.SubElement(elem, type_tag)
            elem.text = si.rock_type_detail

    def _bind_preferences(self):
        prefid = 'pychron.igsn'
        # bind_preference(self, 'url', '{}.url'.format(prefid))
        bind_preference(self, 'username', '{}.username'.format(prefid))
        bind_preference(self, 'password', '{}.password'.format(prefid))
        bind_preference(self, 'user_code', '{}.user_code'.format(prefid))

    def _get_value(self, obj, attr, iattr, required):
        val = None

        if not iattr:
            iattr = attr

        try:
            val = str(getattr(obj, iattr))
        except AttributeError:
            if required:
                self.warning_dialog('Required attribute "{}" not supplied. Contact developer'.format(attr))

        return val


if __name__ == '__main__':
    igsn = IGSNService(bind=False,
                       usercode='IENMT',
                       username=os.environ.get('GeoPassUsername'),
                       password=os.environ.get('GeoPassPassword'))
    name = 'foo'
    material = 'bar'
    igsn.get_new_igsn(name, material)
    # print igsn._assemble_content(sample)
# ============= EOF =============================================
