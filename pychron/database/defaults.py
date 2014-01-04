#===============================================================================
# Copyright 2011 Jake Ross
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
import struct
import os

from pychron.spectrometer.molecular_weights import MOLECULAR_WEIGHTS
from pychron.paths import paths


def iterdir(d, exclude=None):
    #if exclude is None:
    #    exclude =tuple()

    for t in os.listdir(d):
        p = os.path.join(d, t)
        #print os.path.isfile(p), p

        if t.startswith('.'):
            continue

        if exclude:
            _, ext = os.path.splitext(t)
            if ext in exclude:
                continue

        if not os.path.isfile(p):
            continue

        yield p, t


def load_isotopedb_defaults(db):
    with db.session_ctx() as sess:
        for name, mass in MOLECULAR_WEIGHTS.iteritems():
            db.add_molecular_weight(name, mass)

        for at in ['blank_air',
                   'blank_cocktail',
                   'blank_unknown',
                   'background', 'air', 'cocktail', 'unknown']:
        #                           blank', 'air', 'cocktail', 'background', 'unknown']:
            db.add_analysis_type(at)

        for mi in ['obama', 'jan', 'nmgrl map']:
            db.add_mass_spectrometer(mi)

        project = db.add_project('references')
        #print project
        for i, di in enumerate(['blank_air',
                                'blank_cocktail',
                                'blank_unknown',
                                'background', 'air', 'cocktail']):
            samp = db.add_sample(di, project=project)
            #print samp.id, samp, project.id
            #            samp.project = project
            #samp.project_id=project.id
            #print samp.project_id
            db.add_labnumber(i + 1, sample=samp)
        sess.commit()

        for hi, kind, make in [('Fusions CO2', '10.6um co2', 'photon machines'),
                               ('Fusions Diode', '810nm diode', 'photon machines'),
                               ('Fusions UV', '193nm eximer', 'photon machines')
        ]:
            db.add_extraction_device(name=hi,
                                     kind=kind,
                                     make=make,
            )

        mdir = os.path.join(paths.setup_dir, 'irradiation_tray_maps')
        mdir=paths.irradiation_tray_maps_dir
        # if not os.path.isdir(mdir):
        #     if information(None, 'No irradiation_tray_maps directory. add to .../setupfiles'):
        #         try:
        #             os.mkdir(mdir)
        #         except OSError,e:
        #             warning(None, 'Failed making {}: error={}'.format(mdir, e))
        #
        # else:
        for p, name in iterdir(mdir, exclude=('.zip',)):
            load_irradiation_map(db, p, name)

        mdir = paths.map_dir
        for p, name in iterdir(mdir):
            _load_tray_map(db, p, name)

        for t in ('ok', 'invalid'):
            db.add_tag(t, user='default')


def _load_tray_map(db, p, name):
    from pychron.lasers.stage_managers.stage_map import StageMap

    sm = StageMap(file_path=p)

    r = sm.g_dimension
    blob = ''.join([struct.pack('>fff', si.x, si.y, r)
                    for si in sm.sample_holes])
    db.add_load_holder(name, geometry=blob)

def parse_irradiation_tray_map(p):
    """
        return list of  x,y,r tuples or None if exception
    """
    try:
        with open(p, 'r') as fp:
            h = fp.readline()
            _, diam = map(str.strip, h.split(','))
            holes = []
            for i, l in enumerate(fp):
                try:
                    args = map(float, l.strip().split(','))
                    if len(args) == 2:
                        r = diam
                    else:
                        r = args[2]

                    holes.append((args[0], args[1], float(r)))

                except ValueError:
                    break

            return holes
    except Exception:
        return


def load_irradiation_map(db, p, name):
    overwrite_geometry = False

    holes=parse_irradiation_tray_map(p)
    if holes is not None:
        try:
            blob = ''.join([struct.pack('>fff', x, y, r) for x, y, r in holes])
            name, _ = os.path.splitext(name)

            h = db.add_irradiation_holder(name, geometry=blob)
            if overwrite_geometry:
                h.geometry = blob
        except Exception, e:
            print p, name, e
            db.sess.rollback()

    # with open(p, 'r') as f:
    #     try:
    #
    #
    #         blob = ''.join([struct.pack('>fff', x, y, r) for x, y, r in holes])
    #         name, _ = os.path.splitext(name)
    #
    #         h = db.add_irradiation_holder(name, geometry=blob)
    #         if overwrite_geometry:
    #             h.geometry = blob
    #
    #     except Exception, e:
    #         print p, name, e
    #         db.sess.rollback()

