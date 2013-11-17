#===============================================================================
# Copyright 2012 Jake Ross
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
from pychron.experiment.automated_run.automated_run import AutomatedRun
#============= standard library imports ========================
#============= local library imports  ==========================

class UVAutomatedRun(AutomatedRun):
    #reprate = Int
    #mask = Str
    #attenuator = Str
    #image = Str

    #    masks = Property
    #    extract_units_names = List([NULL_STR, 'burst', 'continuous'])
    #    _default_extract_units = 'burst'
    #    browser_button = Button('Browse')
    #    run_klass = UVAutomatedRun
    def _setup_context(self, script):
        super(UVAutomatedRun, self)._setup_context(script)
        script.setup_context(reprate=self.spec.reprate,
                             mask=self.spec.mask,
                             attenuator=self.spec.attenuator)


    def _save_extraction(self, analysis):
        ext = super(UVAutomatedRun, self)._save_extraction(analysis)
        if self.image:
            dbim = self.db.get_image(self.image)
            if dbim is None:
                # use media server so only save path of file
                # secondary option- open image and save to db
                dbim = self.db.add_image(self.image,
                                         #                                  image=self.image.tostring()
                )

            ext.image = dbim

        # save snapshot recorded by pyscript
        if self.extraction_script:
            sps = self.extraction_script.snapshot_paths
            if sps:
                for sp in sps:
                    dbsnap = self.db.add_snapshot(sp)
                    ext.snapshots.append(dbsnap)

        return ext

    #    @cached_property
    #    def _get_masks(self):
    #        p = os.path.join(paths.device_dir, 'uv', 'masks.txt')
    #        masks = []
    #        if os.path.isfile(p):
    #            with open(p, 'r') as fp:
    #                for lin in fp:
    #                    lin = lin.strip()
    #                    if not lin or lin.startswith('#'):
    #                        continue
    #                    masks.append(lin)
    #
    #        return masks

    #    def _get_supplemental_extract_group(self):
    #        g = VGroup(Item('reprate'),
    #                   Item('mask', editor=EnumEditor(name='masks')),
    #                   Item('attenuator'),
    #                   HGroup(Item('image', springy=True), Item('browser_button', show_label=False)),
    #                   label='UV'
    #                   )
    #        return g

    def _extraction_script_factory(self, ec, key):
        obj = super(UVAutomatedRun, self)._extraction_script_factory(ec, key)
        obj.setup_context(reprate=self.reprate,
                          mask=self.mask,
                          attenuator=self.attenuator)
        return obj

    def _assemble_extraction_parameters(self, edict):
        edict.update(reprate=self.reprate,
                     mask_name=self.mask,
                     attenuator=self.attenuator)

#    def _image_browser_factory(self):
#        b = self.application.get_service('pychron.media_server.browser.MediaBrowser')
#        if b is not None:
#            c = self.application.get_service('pychron.media_server.client.MediaClient')
#            b.client = c
#
#        return b
##===============================================================================
# # handlers
##===============================================================================
#    def _browser_button_fired(self):
#        browser = self._image_browser_factory()
# #        browser.root='images/fusions_uv'
#        browser.load_remote_directory('images/fusions_uv')
#        info = browser.edit_traits(view='modal_view', kind='livemodal')
#        if info.result:
#            self.image = browser.get_selected_image_name()
#    @cached_property
#    def _get_post_measurement_script(self):
#        self._post_measurement_script = self._load_script('post_measurement')
#        return self._post_measurement_script
#
#    @cached_property
#    def _get_post_equilibration_script(self):
#        self._post_equilibration_script = self._load_script('post_equilibration')
#        return self._post_equilibration_script
#
#    @cached_property
#    def _get_measurement_script(self):
#        self._measurement_script = self._load_script('measurement')
#        return self._measurement_script
#
#    @cached_property
#    def _get_extraction_script(self):
#        self._extraction_script = self._load_script('extraction')
#        return self._extraction_script

#============= EOF =============================================
