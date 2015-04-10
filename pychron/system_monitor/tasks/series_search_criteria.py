from traits.api import HasTraits, Str, Int, List
from traitsui.api import View, VGroup, Item, EnumEditor


class SearchCriteria(HasTraits):
    hours = Int
    weeks = Int
    days = Int
    limit = Int
    mass_spectrometer = Str
    mass_spectrometers = List

    analysis_type = Str
    analysis_types = List

    def traits_view(self):
        v = View(VGroup(VGroup(Item('mass_spectrometer', editor=EnumEditor(name='mass_spectrometers')),
                               Item('analysis_type', editor=EnumEditor(name='analysis_types')),
                               Item('weeks'),
                               Item('days'),
                               Item('hours'),
                               Item('_'),
                               Item('limit'), )),
                 buttons=['OK', 'Cancel'],
                 title='Select Search Criteria',
                 kind='livemodal')
        return v
