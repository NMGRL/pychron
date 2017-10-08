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

# ============= standard library imports ========================
# ============= local library imports  ==========================
LAT_TT = 'Latitude of the location where the sample was collected. Needs to be entered in decimal degrees. ' \
         'Negative values for South latitudes. (Coordinate system: WGS84)'
LONG_TT = 'Longitude of the location where the sample was collected. Needs to be entered in decimal degrees. ' \
          'Negative values for West longitudes. (Coordinate system: WGS84)'
ELEVATION_TT = 'Elevation at which a sample was collected (in meters). Use negative values for depth below sea level'

ROCK_TYPES = ('Igneous', 'Metamorphic', 'Ore', 'Sedimentary', 'Xenolithic')
SUB_ROCK_TYPES = {'Igneous': ('Plutonic', 'Volcanic'),
                  'Metamorphic': [],
                  'Ore': [],
                  'Sedimentary': [],
                  'Xenolithic': []}

ROCK_TYPE_DETAILS = {'Igneous': ('Exotic', 'Felsic', 'Intermediate', 'Mafic', 'Ultramafic'),
                     'Metamorphic': ('Calc-Silicate',
                                     'Eclogite',
                                     'Gneiss',
                                     'Granofels',
                                     'Granulite',
                                     'MechanicallyBroken',
                                     'Meta-Carbonate',
                                     'Meta-Ultramafic',
                                     'Metasedimentary',
                                     'Metasomatic',
                                     'Schist',
                                     'Slate'),
                     'Ore': ('Other',
                             'Oxide',
                             'Sulfide'),
                     'Sedimentary': ('Carbonate',
                                     'ConglomerateAndOrBreccia',
                                     'Evaporite',
                                     'GlacialAndOrPaleosol',
                                     'Hybrid',
                                     'Ironstone',
                                     'MixedCarbAndOrSiliciclastic',
                                     'MnNoduleAndOrCrust',
                                     'SiliceousBiogenic',
                                     'Siliciclastic',
                                     'Volcaniclastic'),
                     'Xenolithic': []}

SAMPLE_TYPES = ('Bead',
                'Chemical Fraction',
                'Core',
                'Core Half Round',
                'Core Piece',
                'Core Quarter Round',
                'Core Section',
                'Core Section Half',
                'Core Sub-Piece',
                'Core Whole Round',
                'CTD',
                'Cube',
                'Culture',
                'Cuttings',
                'Cylinder',
                'Dredge',
                'Gas',
                'Grab',
                'Hole',
                'Individual Sample',
                'Liquid',
                'Mechanical Fraction',
                'Oriented Core',
                'Powder',
                'Rock Powder',
                'Site',
                'Slab',
                'Smear',
                'Specimen',
                'Squeeze Cake',
                'Terrestrial Section',
                'Thin Section',
                'Toothpick',
                'Trawl',
                'U-Channel',
                'Wedge',
                'Other')

SAMPLE_ATTRS = (('user_code', '', True),
                ('sample_type', '', True),
                ('name', '', True),
                ('material', '', True),
                ('description', '', False),
                ('age_min', '', False),
                ('age_max', '', False),
                ('age_unit', '', False),
                ('collection_method', '', False),
                ('latitude', '', False),
                ('longitude', '', False),
                ('elevation', '', False),
                ('primary_location_name', '', False),
                ('country', '', False),
                ('province', '', False),
                ('county', '', False),
                ('collector', '', False),
                ('collection_start_date', '', False),
                ('collection_date_precision', '', False),
                ('original_archive', '', False))

MATERIALS = ('Rock', 'Sediment', 'Soil', 'Synthetic', 'NotApplicable','Other',
             'Biology','Gas','Ice', 'LiquidAqueous', 'LiquidOrganic', 'Mineral',  'Particulate')

# ============= EOF =============================================
