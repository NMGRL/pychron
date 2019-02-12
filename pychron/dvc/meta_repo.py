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
import os
import shutil
from datetime import datetime

# ============= enthought library imports =======================
from traits.api import Bool
from uncertainties import ufloat

from pychron.canvas.utils import iter_geom
from pychron.core.helpers.datetime_tools import ISO_FORMAT_STR
from pychron.core.helpers.filetools import glob_list_directory, add_extension, \
    list_directory
from pychron.core.helpers.strtools import to_bool
from pychron.dvc import dvc_dump, dvc_load, repository_path, list_frozen_productions
from pychron.dvc.meta_object import IrradiationHolder, Chronology, Production, cached, Gains, LoadHolder
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.paths import paths, r_mkdir
from pychron.pychron_constants import INTERFERENCE_KEYS, RATIO_KEYS, DEFAULT_MONITOR_NAME, DATE_FORMAT, NULL_STR


def irradiation_holder_holes(name):
    p = os.path.join(paths.meta_root, 'irradiation_holders', add_extension(name))
    holder = IrradiationHolder(p)
    return holder.holes


def irradiation_chronology(name):
    p = os.path.join(paths.meta_root, name, 'chronology.txt')
    return Chronology(p)


def dump_chronology(path, doses):
    if doses is None:
        doses = []

    with open(path, 'w') as wfile:
        for p, s, e in doses:
            if not isinstance(s, str):
                s = s.strftime(ISO_FORMAT_STR)
            if not isinstance(s, str):
                s = s.strftime(ISO_FORMAT_STR)
            if not isinstance(p, str):
                p = '{:0.3f}'.format(p)

            line = '{},{},{}\n'.format(p, s, e)
            wfile.write(line)


def gain_path(name):
    root = os.path.join(paths.meta_root, 'spectrometers')
    if not os.path.isdir(root):
        os.mkdir(root)

    p = os.path.join(root, add_extension('{}.gain'.format(name), '.json'))
    return p


def get_frozen_productions(repo):
    prods = {}
    for name, path in list_frozen_productions(repo):
        prods[name] = Production(path)

    return prods


def get_frozen_flux(repo, irradiation):
    path = repository_path(repo, '{}.json'.format(irradiation))

    fd = {}
    if path:
        fd = dvc_load(path)
        for fi in fd.values():
            fi['j'] = ufloat(*fi['j'], tag='J')
    return fd


class MetaRepo(GitRepoManager):
    clear_cache = Bool

    def get_monitor_info(self, irrad, level):
        age, decay = NULL_STR, NULL_STR
        positions = self._get_level_positions(irrad, level)
        # assume all positions have same monitor_age/decay constant. Not strictly true. Potential some ambiquity but
        # will not be resolved now 8/26/18.
        if positions:
            position = positions[0]
            opt = position.get('options')
            if opt:
                age = position.get('monitor_age', NULL_STR)

            decayd = position.get('decay_constants')
            if decayd:
                decay = decayd.get('lambda_k_total', NULL_STR)

        return str(age), str(decay)

    def get_molecular_weights(self):
        p = os.path.join(paths.meta_root, 'molecular_weights.json')
        return dvc_load(p)

    def update_molecular_weights(self, wts, commit=False):
        p = os.path.join(paths.meta_root, 'molecular_weights.json')
        dvc_dump(wts, p)
        self.add(p, commit=commit)

    def add_unstaged(self, *args, **kw):
        super(MetaRepo, self).add_unstaged(self.path, **kw)

    def save_gains(self, ms, gains_dict):
        p = gain_path(ms)
        dvc_dump(gains_dict, p)

        if self.add_paths(p):
            self.commit('Updated gains')

    def update_script(self, rootname, name, path_or_blob):
        self._update_text(os.path.join('scripts', rootname.lower()), name, path_or_blob)

    def update_experiment_queue(self, rootname, name, path_or_blob):
        self._update_text(os.path.join('experiments', rootname.lower()), name, path_or_blob)

    def update_level_production(self, irrad, name, prname, note=None):
        prname = prname.replace(' ', '_')

        pathname = add_extension(prname, '.json')

        src = os.path.join(paths.meta_root, irrad, 'productions', pathname)
        if os.path.isfile(src):
            self.update_productions(irrad, name, prname, note=note)
        else:
            self.warning_dialog('Invalid production name'.format(prname))

    def add_production_to_irradiation(self, irrad, name, params, add=True, commit=False):
        self.debug('adding production {} to irradiation={}'.format(name, irrad))
        p = os.path.join(paths.meta_root, irrad, 'productions', add_extension(name, '.json'))
        prod = Production(p, new=not os.path.isfile(p))

        prod.update(params)
        prod.dump()
        if add:
            self.add(p, commit=commit)

    def add_production(self, irrad, name, obj, commit=False, add=True):
        p = self.get_production(irrad, name, force=True)

        p.attrs = attrs = INTERFERENCE_KEYS + RATIO_KEYS
        kef = lambda x: '{}_err'.format(x)

        if obj:
            def values():
                return ((k, getattr(obj, k), kef(k), getattr(obj, kef(k))) for k in attrs)
        else:
            def values():
                return ((k, 0, kef(k), 0) for k in attrs)

        for k, v, ke, e in values():
            setattr(p, k, v)
            setattr(p, ke, e)

        p.dump()
        if add:
            self.add(p.path, commit=commit)

    def update_production(self, prod, irradiation=None):
        ip = self.get_production(prod.name)
        self.debug('saving production {}'.format(prod.name))

        params = prod.get_params()
        for k, v in params.items():
            self.debug('setting {}={}'.format(k, v))
            setattr(ip, k, v)

        ip.note = prod.note

        self.add(ip.path, commit=False)
        self.commit('updated production {}'.format(prod.name))

    def update_productions(self, irrad, level, production, note=None, add=True):
        p = os.path.join(paths.meta_root, irrad, 'productions.json')

        obj = dvc_load(p)
        obj['note'] = str(note) or ''

        if level in obj:
            if obj[level] != production:
                self.debug('setting production to irrad={}, level={}, prod={}'.format(irrad, level, production))
                obj[level] = production
                dvc_dump(obj, p)

                if add:
                    self.add(p, commit=False)
        else:
            obj[level] = production
            dvc_dump(obj, p)
            if add:
                self.add(p, commit=False)

    def set_identifier(self, irradiation, level, pos, identifier):
        p = self.get_level_path(irradiation, level)
        jd = dvc_load(p)
        positions = self._get_level_positions(irradiation, level)

        d = next((p for p in positions if p['position'] == pos), None)
        if d:
            d['identifier'] = identifier
            jd['positions'] = positions

        dvc_dump(jd, p)
        self.add(p, commit=False)

    def get_level_path(self, irrad, level):
        return os.path.join(paths.meta_root, irrad, '{}.json'.format(level))

    def add_level(self, irrad, level, add=True):
        p = self.get_level_path(irrad, level)
        lv = dict(z=0, positions=[])
        dvc_dump(lv, p)
        if add:
            self.add(p, commit=False)

    def add_chronology(self, irrad, doses, add=True):
        p = os.path.join(paths.meta_root, irrad, 'chronology.txt')

        dump_chronology(p, doses)
        if add:
            self.add(p, commit=False)

    def add_irradiation(self, name):
        p = os.path.join(paths.meta_root, name)
        if not os.path.isdir(p):
            os.mkdir(p)

    def add_position(self, irradiation, level, pos, add=True):
        p = self.get_level_path(irradiation, level)
        jd = dvc_load(p)
        if isinstance(jd, list):
            positions = jd
            z = 0
        else:
            positions = jd.get('positions', [])
            z = jd.get('z', 0)

        pd = next((p for p in positions if p['position'] == pos), None)
        if pd is None:
            positions.append({'position': pos, 'decay_constants': {}})

        dvc_dump({'z': z, 'positions': positions}, p)
        if add:
            self.add(p, commit=False)

    def add_irradiation_holder(self, name, blob, commit=False, overwrite=False, add=True):
        root = os.path.join(paths.meta_root, 'irradiation_holders')
        if not os.path.isdir(root):
            os.mkdir(root)
        p = os.path.join(root, add_extension(name))

        if not os.path.isfile(p) or overwrite:
            with open(p, 'w') as wfile:
                holes = list(iter_geom(blob))
                n = len(holes)
                wfile.write('{},0.0175\n'.format(n))
                for idx, (x, y, r) in holes:
                    wfile.write('{:0.4f},{:0.4f},{:0.4f}\n'.format(x, y, r))
            if add:
                self.add(p, commit=commit)

    def get_load_holders(self):
        p = os.path.join(paths.meta_root, 'load_holders')
        return list_directory(p, extension='.txt', remove_extension=True)

    def add_load_holder(self, name, path_or_txt, commit=False, add=True):
        p = os.path.join(paths.meta_root, 'load_holders', name)
        if os.path.isfile(path_or_txt):
            shutil.copyfile(path_or_txt, p)
        else:
            with open(p, 'w') as wfile:
                wfile.write(path_or_txt)
        if add:
            self.add(p, commit=commit)

    def update_level_z(self, irradiation, level, z):
        p = self.get_level_path(irradiation, level)
        obj = dvc_load(p)

        try:
            add = obj['z'] != z
            obj['z'] = z
        except TypeError:
            obj = {'z': z, 'positions': obj}
            add = True

        dvc_dump(obj, p)
        if add:
            self.add(p, commit=False)

    def remove_irradiation_position(self, irradiation, level, hole):
        p = self.get_level_path(irradiation, level)
        jd = dvc_load(p)
        if jd:
            if isinstance(jd, list):
                positions = jd
                z = 0
            else:
                positions = jd['positions']
                z = jd['z']

            npositions = [ji for ji in positions if not ji['position'] == hole]
            obj = {'z': z, 'positions': npositions}
            dvc_dump(obj, p)
            self.add(p, commit=False)

    def update_fluxes(self, irradiation, level, j, e, add=True):
        p = self.get_level_path(irradiation, level)
        jd = dvc_load(p)

        if isinstance(jd, list):
            positions = jd
        else:
            positions = jd.get('positions')

        if positions:
            for ip in positions:
                ip['j'] = j
                ip['j_err'] = e

            dvc_dump(jd, p)
            if add:
                self.add(p, commit=False)

    def update_flux(self, irradiation, level, pos, identifier, j, e, mj, me, decay=None,
                    position_jerr=None,
                    analyses=None, options=None, add=True):

        if options is None:
            options = {}

        if decay is None:
            decay = {}
        if analyses is None:
            analyses = []

        p = self.get_level_path(irradiation, level)
        jd = dvc_load(p)
        if isinstance(jd, list):
            positions = jd
            z = 0
        else:
            positions = jd.get('positions', [])
            z = jd.get('z', 0)

        npos = {'position': pos, 'j': j, 'j_err': e,
                'mean_j': mj, 'mean_j_err': me,
                'position_jerr': position_jerr,
                'decay_constants': decay,
                'identifier': identifier,
                'options': options,
                'analyses': [{'uuid': ai.uuid,
                              'record_id': ai.record_id,
                              'status': ai.is_omitted()}
                             for ai in analyses]}
        if positions:
            added = any((ji['position'] == pos for ji in positions))
            npositions = [ji if ji['position'] != pos else npos for ji in positions]
            if not added:
                npositions.append(npos)
        else:
            npositions = [npos]

        obj = {'z': z, 'positions': npositions}
        dvc_dump(obj, p)
        if add:
            self.add(p, commit=False)

    def update_chronology(self, name, doses):
        p = os.path.join(paths.meta_root, name, 'chronology.txt')
        dump_chronology(p, doses)

        self.add(p, commit=False)

    def get_irradiation_holder_names(self):
        return glob_list_directory(os.path.join(paths.meta_root, 'irradiation_holders'),
                                   extension='.txt',
                                   remove_extension=True)

    def get_cocktail_irradiation(self):
        """
        example cocktail.json

        {
            "chronology": "2016-06-01 17:00:00",
            "j": 4e-4,
            "j_err": 4e-9
        }

        :return:
        """
        p = os.path.join(paths.meta_root, 'cocktail.json')
        ret = dvc_load(p)
        nret = {}
        if ret:
            lines = ['1.0, {}, {}'.format(ret['chronology'], ret['chronology'])]
            c = Chronology.from_lines(lines)
            nret['chronology'] = c
            nret['flux'] = ufloat(ret['j'], ret['j_err'])

        return nret

    def get_default_productions(self):
        p = os.path.join(paths.meta_root, 'reactors.json')
        if not os.path.isfile(p):
            with open(p, 'w') as wfile:
                from pychron.file_defaults import REACTORS_DEFAULT
                wfile.write(REACTORS_DEFAULT)

        return dvc_load(p)

    def get_flux_positions(self, irradiation, level):
        positions = self._get_level_positions(irradiation, level)
        return positions

    def get_flux(self, irradiation, level, position):
        positions = self.get_flux_positions(irradiation, level)
        return self.get_flux_from_positions(position, positions)

    def get_flux_from_positions(self, position, positions):
        j, je, pe, lambda_k = 0, 0, 0, None
        monitor_name, monitor_material, monitor_age = DEFAULT_MONITOR_NAME, 'sanidine', ufloat(28.201, 0)
        if positions:
            pos = next((p for p in positions if p['position'] == position), None)
            if pos:
                j, je, pe = pos.get('j', 0), pos.get('j_err', 0), pos.get('position_jerr', 0)
                dc = pos.get('decay_constants')
                if dc:
                    # this was a temporary fix and likely can be removed
                    if isinstance(dc, float):
                        v, e = dc, 0
                    else:
                        v, e = dc.get('lambda_k_total', 0), dc.get('lambda_k_total_error', 0)
                    lambda_k = ufloat(v, e)
                mon = pos.get('monitor')
                if mon:
                    monitor_name = mon.get('name', DEFAULT_MONITOR_NAME)
                    sa = mon.get('age', 28.201)
                    se = mon.get('error', 0)
                    monitor_age = ufloat(sa, se, tag='monitor_age')
                    monitor_material = mon.get('material', 'sanidine')

        fd = {'j': ufloat(j, je, tag='J'),
              'position_jerr': pe,
              'lambda_k': lambda_k,
              'monitor_name': monitor_name,
              'monitor_material': monitor_material,
              'monitor_age': monitor_age}
        return fd

    def get_gains(self, name):
        g = self.get_gain_obj(name)
        return g.gains

    def save_sensitivities(self, sens):
        ps = []
        for k, v in sens.items():
            root = os.path.join(paths.meta_root, 'spectrometers')
            p = os.path.join(root, add_extension('{}.sens'.format(k), '.json'))
            dvc_dump(v, p)
            ps.append(p)

        if self.add_paths(ps):
            self.commit('Updated sensitivity')

    def get_sensitivities(self):
        specs = {}
        root = os.path.join(paths.meta_root, 'spectrometers')
        for p in list_directory(root):
            if p.endswith('.sens.json'):
                name = p.split('.')[0]
                p = os.path.join(root, p)
                obj = dvc_load(p)

                specs[name] = obj
                for r in obj:
                    if r['create_date']:
                        r['create_date'] = datetime.strptime(r['create_date'], DATE_FORMAT)

        return specs

    def get_sensitivity(self, name):
        sens = self.get_sensitivities()
        spec = sens.get(name)
        v = 1
        if spec:
            v = spec.get('sensitivity', 1)
        return v

    @cached('clear_cache')
    def get_gain_obj(self, name, **kw):
        p = gain_path(name)
        return Gains(p)

    # @cached('clear_cache')
    def get_production(self, irrad, level, **kw):
        path = os.path.join(paths.meta_root, irrad, 'productions.json')
        obj = dvc_load(path)

        pname = obj.get(level, '')
        p = os.path.join(paths.meta_root, irrad, 'productions', add_extension(pname, ext='.json'))

        ip = Production(p)
        # print 'new production id={}, name={}, irrad={}, level={}'.format(id(ip), pname, irrad, level)
        return pname, ip

    # @cached('clear_cache')
    def get_chronology(self, name, **kw):

        chron = irradiation_chronology(name)

        chron.use_irradiation_endtime = to_bool(self.application.preferences.get(
            'pychron.arar.constants.use_irradiation_endtime', False))

        return chron

    @cached('clear_cache')
    def get_irradiation_holder_holes(self, name, **kw):
        return irradiation_holder_holes(name)

    @cached('clear_cache')
    def get_load_holder_holes(self, name, **kw):
        p = os.path.join(paths.meta_root, 'load_holders', add_extension(name))
        holder = LoadHolder(p)
        return holder.holes

    @property
    def sensitivity_path(self):
        return os.path.join(paths.meta_root, 'sensitivity.json')

    # private
    def _get_level_positions(self, irrad, level):
        p = self.get_level_path(irrad, level)
        obj = dvc_load(p)
        if isinstance(obj, list):
            positions = obj
        else:
            positions = obj.get('positions', [])
        return positions

    def _update_text(self, tag, name, path_or_blob):
        if not name:
            self.debug('cannot update text with no name. tag={} name={}'.format(tag, name))
            return

        root = os.path.join(paths.meta_root, tag)
        if not os.path.isdir(root):
            r_mkdir(root)

        p = os.path.join(root, name)
        if os.path.isfile(path_or_blob):
            shutil.copyfile(path_or_blob, p)
        else:
            with open(p, 'w') as wfile:
                wfile.write(path_or_blob)

        self.add(p, commit=False)

# ============= EOF =============================================
