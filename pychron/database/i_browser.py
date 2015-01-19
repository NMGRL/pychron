from traits.has_traits import Interface

__author__ = 'argonlab2'


class IBrowser(Interface):
    def get_mass_spectrometers(self):
        pass
    def get_analysis_types(self):
        pass
    def get_get_extraction_devices(self):
        pass
    def get_project_labnumbers(self, project_names, filter_non_run, low_post=None, high_post=None,
                               analysis_types=None, mass_spectrometers=None):
        pass
    def get_labnumber_analyses(self, lns, low_post=None, high_post=None,
                               omit_key=None, exclude_uuids=None, mass_spectrometers=None, **kw):
        pass