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
from traitsui.api import View, VGroup, Item, EnumEditor, Tabbed, UItem, HGroup, TextEditor

from pychron.core.ui.preference_binding import bind_preference
from pychron.igsn.definitions import SAMPLE_ATTRS, SAMPLE_TYPES, ROCK_TYPES, SUB_ROCK_TYPES, ROCK_TYPE_DETAILS, LAT_TT, \
    ELEVATION_TT, LONG_TT, MATERIALS
from pychron.loggable import Loggable


class IGSNSampleModel(HasTraits):
    user_code = Str

    sample_type = Enum(SAMPLE_TYPES)
    name = Str
    material = Enum(MATERIALS)
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

    xml_content = Str

    def __init__(self, *args, **kw):
        super(IGSNSampleModel, self).__init__(*args, **kw)

        dt = datetime.now()
        self._collection_start_date = dt.date()
        self._collection_start_time = dt.time()
        self.timezone = 'US/Mountain'

    def assemble_content(self):
        xmlns = 'http://app.geosamples.org'
        xsi = 'http://www.w3.org/2001/XMLSchema-instance'
        nsmap = {None: xmlns,
                 'xsi': xsi}

        schema_uri = "http://app.geosamples.org/samplev2.xsd "
        root = etree.Element('samples', nsmap=nsmap)
        root.set('{{{}}}schemaLocation'.format(xsi), schema_uri)
        self._add_sample(root)

        content = etree.tostring(root, xml_declaration=True, pretty_print=True)
        self.xml_content = content
        return content

    def _add_sample(self, root):
        se = etree.SubElement(root, 'sample')
        self._add_classification(se)

        for tag, iattr, required in SAMPLE_ATTRS:
            if tag == 'user_code':
                val = self.user_code
            else:
                val = self._get_value(tag, iattr, required)

            if val:
                elem = etree.SubElement(se, tag)
                elem.text = self._get_value(tag, iattr, required)

    def _add_classification(self, se):
        clf = etree.SubElement(se, 'classification')
        rock = etree.SubElement(clf, 'Rock')

        elem = etree.SubElement(rock, self.rock_type)
        type_tag = '{}Type'.format(self.rock_type)
        if self.sub_rock_type:
            elem = etree.SubElement(elem, self.sub_rock_type)
            type_tag = '{}Type'.format(self.sub_rock_type)

        if self.rock_type_detail:
            elem = etree.SubElement(elem, type_tag)
            elem.text = self.rock_type_detail

    def _get_value(self, attr, iattr, required):
        val = None

        if not iattr:
            iattr = attr

        try:
            val = str(getattr(self, iattr))
        except AttributeError:
            if required:
                self.warning_dialog('Required attribute "{}" not supplied. Contact developer'.format(attr))

        return val

    def _anytrait_changed(self, name, old, new):
        self.assemble_content()

    @property
    def collection_start_date(self):
        if self._collection_start_date and self._collection_start_time:
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

        v = View(Tabbed(VGroup(Item('user_code', label='SESAR User Code', style='readonly'),
                               required_grp, classification_grp, optional_grp,
                               label='New Sample'),
                        VGroup(UItem('xml_content',
                                     style='custom',
                                     editor=TextEditor(read_only=True)), label='XML')),
                 title='New IGSN',
                 resizable=True,
                 buttons=['OK', 'Cancel'])
        return v


class IGSNService(Loggable):
    # uri = 'https://app.geosamples.org/webservices/upload.php'
    # url = 'https://sesardev.geosamples.org/webservices/upload.php'
    # base_url = 'https://app.geosamples.org'
    base_url = 'https://sesardev.geosamples.org'
    username = Str
    password = Str
    user_code = Str

    def __init__(self, bind=True, *args, **kw):
        super(IGSNService, self).__init__(*args, **kw)
        if bind:
            self._bind_preferences()

    def get_new_igsn(self, sample='', material='Rock'):

        igsn = None
        # if sample:
            # check for existing igsn
            # eigsns = self.get_existing_igsn(sample)
            # if eigsns:
            #     self.information_dialog('Existing IGSN for sample: {} igsn: {}'.format(sample, ','.join(eigsns)))
            #     return

        if igsn is None:

            model = IGSNSampleModel(name=sample, material=material,
                                    user_code=self.user_code,
                                    sample_type='Individual Sample')

            info = model.edit_traits(kind='livemodal')
            if not info.result:
                return

            content = model.assemble_content()
            locator = 'webservices/upload.php'
            r = self._post(locator,
                           data={'content': content})

            igsn = self._parse_response(r, single=True)

        return igsn

    def get_existing_igsn(self, sample):
        igsns = self.get_user_code_igsns()
        if igsns:
            existing = []
            for igsn in igsns:
                iigsn = self.get_igsn(igsn)
                if iigsn:
                    sample_name = iigsn['sample']['name']
                    if sample_name == sample:
                        existing.append(igsn)
            return existing

    def get_igsn(self, igsn):
        locator = 'sample/igsn/{}'.format(igsn)
        headers = {'accept': 'application/json'}

        resp = self._post(locator, headers=headers)
        if resp.status_code == 200:
            return resp.json()

    def get_user_code_igsns(self, user_code=None):
        if user_code is None:
            user_code = self.user_code

        locator = 'samples/user_code/{}'.format(user_code)
        headers = {'accept': 'application/json'}

        igsns = []
        while 1:
            resp = self._post(locator, headers=headers)
            if resp.status_code == 200:
                jd = resp.json()
                igsns.extend(jd['igsn_list'])
                locator = jd.get('next_list')
                if not locator:
                    break
            else:
                break

        return igsns

    def _post(self, locator, data=None, headers=None):
        if headers is None:
            headers = {}
        if data is None:
            data = {}

        data['username'] = self.username
        data['password'] = self.password

        url = '{}/{}'.format(self.base_url, locator)
        return requests.post(url, data=data, headers=headers)

    def _parse_response(self, r, single=False):
        # status_code = 200
        # text = '<results><valid code="InvalidAuth">no</valid><error>Please enter your username and password.</error></results>'
        # text = '<results> <sample> <status>Sample [Lulin Upload Status Sample test] was saved successfully with IGSN ' \
        #        '[LLS00009I].</status> <name>Lulin Upload Status Sample test</name> <igsn>LLS00009I' \
        #        '</igsn> </sample> </results>'

        text = r.text
        status_code = r.status_code
        tree = etree.parse(StringIO(text))
        igsns = []

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
            print error.text
            self.warning_dialog('Failed Getting a new IGSN.\nError={}'.format(error.text))

        return igsns

    def _bind_preferences(self):
        prefid = 'pychron.igsn'
        # bind_preference(self, 'url', '{}.url'.format(prefid))
        bind_preference(self, 'username', '{}.username'.format(prefid))
        bind_preference(self, 'password', '{}.password'.format(prefid))
        bind_preference(self, 'user_code', '{}.user_code'.format(prefid))


if __name__ == '__main__':
    igsn = IGSNService(bind=False,
                       user_code='IENMT',
                       username=os.environ.get('GeoPassUsername'),
                       password=os.environ.get('GeoPassPassword'))
    name = 'foo'
    # material = 'Bar'
    print igsn.get_new_igsn(name)
    # print igsn._assemble_content(sample)
# ============= EOF =============================================
