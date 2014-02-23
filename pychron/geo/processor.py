#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================

#============= standard library imports ========================
#============= local library imports  ==========================
import os

from chaco.pdf_graphics_context import PdfPlotGraphicsContext
import yaml

from pychron.canvas.canvas2D.strat_canvas import StratCanvas
from pychron.core.helpers.filetools import unique_path
from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.paths import paths


def strat_ok(s1, s2):
    """
        - s2
        - s1

        strat ok if a1-e1 < a2-e2
    """
    a1 = s1['age']
    e = s1['age_err']
    mswd = s1['mswd']

    e1 = e * 2 * mswd ** 0.5

    a2 = s2['age']
    e = s2['age_err']
    mswd = s2['mswd']
    e2 = e * 2
    if a1 - e1 <= a2 + e2:
        # print a1+e1, a2-e2
        # print 'overlap'
        return True
    else:
        # print 'ff', a2+e2<a1+e1
        # print a1,e1, a2,e2,a1+e1<a2-e2
        return a1 + e1 > a2 - e2


class GeoProcessor(IsotopeDatabaseManager):
    def make_strat_canvas_file(self):
        identifiers = ['57737',
                       '57736',
                       '57744',
                       '57743',
                       '57725',
                       '58627']
        db = self.db

        root = os.path.join(paths.dissertation,
                            'data', 'minnabluff', 'strat_sequences')
        p, _ = unique_path(root, 'seq1', extension='.yaml')

        with db.session_ctx():
            items = []
            for i in identifiers:
                strat = {}
                ln = db.get_labnumber(i)
                sample = ln.sample

                ia = ln.selected_interpreted_age.interpreted_age
                if ia.age_kind != 'Integrated':
                    strat['elevation'] = sample.elevation

                    mat = sample.material.name
                    strat['label'] = '{}({}) {}+/-{} ({})'.format(sample.name,
                                                                  mat,
                                                                  ia.age, ia.age_err,
                                                                  ia.age_kind)
                    strat['age'] = ia.age
                    strat['age_err'] = ia.age_err
                    strat['mswd'] = ia.mswd

                    items.append(strat)

            syd = sorted(items, key=lambda x: x['elevation'])
            for i, yi in enumerate(syd[:-1]):
                # print i, yi['elevation'], yi['age']
                # ee2=2*yi['age_err']*yi['mswd']**0.5
                if not strat_ok(yi, syd[i + 1]):
                    yi['color'] = 'red'

        yd = dict(options={},
                  items=items
        )
        with open(p, 'w') as fp:
            yaml.dump(yd, fp, default_flow_style=False)

        s = StratCanvas()
        s.load_scene(yd)

        p, _ = unique_path(root, 'seq1', extension='.pdf')
        g = PdfPlotGraphicsContext(
            filename=p)

        s.do_layout(size=(500, 700),
                    force=True)

        g.render_component(s)
        g.save()



        #============= EOF =============================================

