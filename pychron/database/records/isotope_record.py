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
import time
from traits.api import HasTraits

#============= standard library imports ========================
# import re
#============= local library imports  ==========================
from pychron.experiment.utilities.identifier import make_runid


class IsotopeRecordView(HasTraits):
    group_id = 0
    graph_id = 0
    mass_spectrometer = ''
    extract_device = ''
    analysis_type = ''
    uuid = ''
    sample = ''
    sample = ''

    iso_fit_status = False
    blank_fit_status = False
    ic_fit_status = False
    flux_fit_status = False

    tag = ''
    temp_status = 0

    record_id = ''
    def set_tag(self, tag):
        self.tag=tag.name

    def create(self, dbrecord):
#        print 'asdfsadfsdaf', dbrecord, dbrecord.labnumber, dbrecord.uuid
        try:
            if dbrecord is None or not dbrecord.labnumber:
                return
            
            ln = dbrecord.labnumber
            self.labnumber = str(ln.identifier)
            self.aliquot = dbrecord.aliquot
            self.step = dbrecord.step
            self.uuid = dbrecord.uuid
            self.tag = dbrecord.tag or ''
            self.rundate = dbrecord.analysis_timestamp
            self.timestamp = time.mktime(self.rundate.timetuple())

            self.record_id = make_runid(self.labnumber, self.aliquot, self.step)
            #            print self.record_id, self.uuid

            if ln.sample:
                self.sample = ln.sample.name
            if dbrecord.labnumber.sample:
                self.sample = dbrecord.labnumber.sample.name

            irp = ln.irradiation_position
            if irp is not None:
                irl = irp.level
                ir = irl.irradiation
                self.irradiation_info = '{}{} {}'.format(ir.name, irl.name, irp.position)

            else:
                self.irradiation_info = ''

            meas = dbrecord.measurement
            if meas is not None:
                self.mass_spectrometer = meas.mass_spectrometer.name.lower()
                if meas.analysis_type:
                    self.analysis_type = meas.analysis_type.name
            ext = dbrecord.extraction
            if ext:
                if ext.extraction_device:
                    self.extract_device = ext.extraction_device.name

            self.flux_fit_status = self._get_flux_fit_status(dbrecord)
            self.blank_fit_status = self._get_selected_history_item(dbrecord, 'selected_blanks_id')
            self.ic_fit_status = self._get_selected_history_item(dbrecord, 'selected_det_intercal_id')
            self.iso_fit_status = self._get_selected_history_item(dbrecord, 'selected_fits_id')

            return True
        except Exception, e:
            import traceback

            traceback.print_exc()
            print e

    def to_string(self):
        return '{} {} {} {}'.format(self.labnumber, self.aliquot, self.timestamp, self.uuid)

    def _get_flux_fit_status(self, item):
        labnumber = item.labnumber
        return 'X' if labnumber.selected_flux_id else ''

    def _get_selected_history_item(self, item, key):
        sh = item.selected_histories
        return ('X' if getattr(sh, key) else '') if sh else ''

        #============= EOF =============================================

#
# def DBProperty():
#     return Property(depends_on='_dbrecord')
#
#
# # class IsotopeRecord(DatabaseRecord, ArArAge):
# class IsotopeRecord(ArArAge):
#     dbrecord = Property(depends_on='_dbrecord')
#     _dbrecord = Any
# #    title_str = 'Analysis'
# #    window_height = 500
# #    window_width = 875
#     color = 'black'
#     isotope_keys = Property
#     isotope_fits = Property
#
#     record_id = Property
#
#     peak_center_graph = Instance(Graph)
#
# #     analysis_summary = Instance(AnalysisSummary)
#
#     sample = DBProperty()
#     material = DBProperty()
#     labnumber = DBProperty()
#     project = DBProperty()
#     shortname = DBProperty()
#     analysis_type = DBProperty()
#     mass_spectrometer = DBProperty()
#     position = DBProperty()
#     extract_device = DBProperty()
#     extract_units = DBProperty()
#
#     '''
#         ic factor should belong to each detector
#
#         this ic_factor is the 40-36(CDD) factor, but its necessary
#         to specify other ic's such as 40-39(AX).
#
#         also should be able to specify reference detector ie H1
#     '''
# #     ic_factor = DBProperty()
#     discrimination = DBProperty()
#
#
#     irradiation = DBProperty()
#     status = DBProperty()
#     peak_center_dac = DBProperty()
#
#     aliquot = DBProperty()
#     step = DBProperty()
#
# #    comment = DBProperty()
# #    extract_value = DBProperty()
# #    extract_duration = DBProperty()
# #    cleanup_duration = DBProperty()
# #    experiment = DBProperty()
# #    extraction = DBProperty()
# #    measurement = DBProperty()
# #    uuid = DBProperty()
#
#     changed = Event
#     item_width = 760
#
#     loaded = False
#
# #     def initialize(self):
# #         self.age_dirty = True
# #         self.load_isotopes()
# #         self.calculate_age()
# #        self.load()
# #         self.load_age()
# #         return True
#
#     def load_age(self):
#         self.age_dirty = True
#         self.load_isotopes()
#         self.debug('load_age {} - {}'.format(self.record_id, self.age))
#
#     def add_note(self, text):
#         db = self.selector.db
#         note = db.add_note(self.dbrecord, text)
#         db.commit()
#         return note
#
#     def save(self):
#         pass
# #        fit_hist = None
# #        db = self.selector.db
# # #        sess = db.get_session()
# # #        db.sess = db.new_session()
# #
# # #        sess.expunge_all()
# #        # save the fits
# #        for fi in self.signal_graph.fit_selector.fits:
# #            # get database fit
# #            dbfit = self._get_db_fit(fi.name)
# #            if dbfit != fi.fit:
# #                if fit_hist is None:
# # #                    fit_hist = proc_FitHistoryTable(analysis=self.dbrecord,
# # #                                                    user=db.save_username
# # #                                                    )
# # #                    self.dbrecord.fit_histories.append(fit_hist)
# # #                    selhist = self.dbrecord.selected_histories
# # #                    selhist.selected_fits = fit_hist
# #                    print db.save_username, 'adsfasfd'
# #                    fit_hist = db.add_fit_history(self.dbrecord, user=db.save_username)
# #
# #                dbiso = next((iso for iso in self.dbrecord.isotopes
# #                              if iso.molecular_weight.name == fi.name), None)
# #
# #                db.add_fit(fit_hist, dbiso, fit=fi.fit)
# # #                _f = proc_FitTable(history=fit_hist, fit=fi.fit)
# #
# #        db.commit()
#
#     def set_status(self, status):
#         self.dbrecord.status = status
#
# #    def fit_isotope(self, name, fit, kind):
# #        iso = self.isotopes[name]
# #        if kind == 'baseline':
# #            iso = iso.baseline
# #
# #        iso.fit
# # #        si = self.signals[name]
# # #        if len(si.xs) < 1:
# # #            data = self._get_peak_time_data(kind, names=[name])
# # #            _det, _iso, _fit, (x, y) = data[name]
# # #            si.xs = x
# # #            si.ys = y
# #
# # #        si.fit = fit
# #
# #        return float(iso.value), float(iso.error)
#
# #     def set_isotope(self, k, v, e):
# #         if self.isotopes.has_key(k):
# #             self.isotopes[k].trait_set(value=v, error=e)
# #         else:
# #             self.isotopes[k] = Isotope(value=v, error=e)
#
#     def set_temporary_blank(self, k, v, e):
#         if self.isotopes.has_key(k):
#             iso = self.isotopes[k]
#             iso.temporary_blank = Blank(value=v, error=e)
#
# #     def set_blank(self, k, v, e):
# #         blank = None
# #         if self.isotopes.has_key(k):
# #             blank = self.isotopes[k].blank
# #
# #         if blank is None:
# #             self.isotopes[k].blank = Blank(value=v, error=e)
# #         else:
# #             blank.trait_set(value=v, error=e)
# #
# #     def set_background(self, k, v, e):
# #         background = None
# #         if self.isotopes.has_key(k):
# #             background = self.isotopes[k].background
# #
# #         if background is None:
# #             self.isotopes[k].background = Background(value=v, error=e)
# #         else:
# #             background.trait_set(value=v, error=e)
#
#     def get_baseline(self, k):
#         print 'get baseline'
#         if self.isotopes.has_key(k):
#             bs = self.isotopes[k].baseline
#             if bs:
#                 return bs.uvalue
# #===============================================================================
# # viewable
# #===============================================================================
# #    def opened(self, ui):
# #        def d():
# # # #            self.selected = None
# #            self.selected = 'summary'
# #        do_later(d)
# # #        self.selected = 'summary'
# # #        self.selected = 'notes'
# # #        self.selected = 'error'
# #        super(IsotopeRecord, self).opened(ui)
#
# #    def closed(self, isok):
# #        self.selected = None
#
#
# #===============================================================================
# # database record
# #===============================================================================
#     def load_result(self):
#         '''
#             load the saved result from the db
#         '''
#         if self.dbrecord:
#             for iso in self.dbrecord.isotopes:
#                 if iso.kind == 'signal':
#                     result = None
#                     if iso.results:
#                         result = iso.results[-1]
#
#
#     def _load_signals(self, dbr, unpack):
#         isotopes = dict()
#
#         for iso in dbr.isotopes:
#             if not iso.kind == 'signal' or not iso.molecular_weight:
#                 continue
#
#             result = None
#             if iso.results:
#                 result = iso.results[-1]
#
#             name = iso.molecular_weight.name
#             if name not in isotopes:
#                 det = iso.detector.name
#                 r = Isotope(dbrecord=iso,
#                             dbresult=result,
#                             name=name,
#                             detector=det,
# #                             refit=refit
#                             unpack=unpack
#                             )
#
#                 fit = None
#                 fit = self._get_db_fit(name, 'signal')
#                 if fit is None:
#                     fit = Fit(fit='linear', filter_outliers=True,
#                               filter_outlier_iterations=1,
#                               filter_outlier_std_devs=2)
#                 r.set_fit(fit)
#                 isotopes[name] = r
#
#         self.isotopes = isotopes
#
#     def _load_baselines_sniffs(self, dbr):
#
#         isotopes = self.isotopes
#
#         for dbiso in dbr.isotopes:
#             if not dbiso.molecular_weight:
#                 continue
#
#             name = dbiso.molecular_weight.name
#             det = dbiso.detector.name
#
#             iso = isotopes[name]
#
#             kw = dict(
#                       dbrecord=dbiso,
#                       name=name, detector=det)
#             if dbiso.kind == 'baseline':
#                 result = None
#                 if dbiso.results:
#                     result = dbiso.results[-1]
#
#                 r = Baseline(dbresult=result,
#                              **kw)
#                 fit = self._get_db_fit(name, 'baseline')
#                 if fit is None:
#                     fit = Fit(fit='average_sem', filter_outliers=True,
#                               filter_outlier_iterations=1,
#                               filter_outlier_std_devs=2)
#                 r.set_fit(fit)
#                 iso.baseline = r
#
#             elif dbiso.kind == 'sniff':
#                 r = Sniff(**kw)
#                 iso.sniff = r
#
#
#     def _load_blanks(self):
#         isotopes = self.isotopes
#         blanks = self._get_blanks()
#
#         keys = isotopes.keys()
#         if blanks:
#             for bi in blanks:
#                 for ba in bi.blanks:
#                     isok = ba.isotope
#                     if isok in keys and isotopes.has_key(isok):
#                         r = Blank(dbrecord=ba, name=isok)
#                         isotopes[isok].blank = r
#                         keys.remove(isok)
#                         if not keys:
#                             break
#
#                 if not keys:
#                     break
#
# #     @profile
#     def load_isotopes(self, unpack=True):
#         dbr = self.dbrecord
#         if dbr and not self.loaded:
#             self._load_signals(dbr, unpack)
#             '''
#
#                 load signals first then baseline and sniffs.
#                 loading signals populates isotopes dict with new Isotope objects
#             '''
#             self._load_baselines_sniffs(dbr)
#             self._load_blanks()
#             self.loaded = True
#
#             return True
#
# #    def load(self):
# # #        self.load_isotopes()
# # #        print self.isotope_keys, self.isotopes
# # #        print self.dbrecord
# #
# # #        timethis(self._make_signal_graph, msg='signal')
# # #        timethis(self._make_baseline_graph, msg='baseline')
# #        self._make_signal_graph()
# #        self._make_baseline_graph()
# #
# #        peakcenter = self._get_peakcenter()
# #        if peakcenter:
# # #            self.categories.insert(-1, 'peak center')
# # #            self.categories.append('peak center')
# #            graph = self._make_peak_center_graph(*peakcenter)
# #            self.peak_center_graph = graph
# #
# # #        blanks = self._get_blanks()
# # #        if blanks:
# # #            for bi in blanks:
# # #                for ba in bi.blanks:
# # #                    r = Blank(dbrecord=ba, name=ba.isotope)
# # #                    self.isotopes[ba.isotope].blank = r
# #
# # #            if 'blanks' not in self.categories:
# # #                self.categories.append(-1, 'blanks')
# # #                self.categories.append('blanks')
# #
# # #        backgrounds = self._get_backgrounds()
# # #        if backgrounds:
# # #            if 'backgrounds' not in self.categories:
# # # #                self.categories.insert(-1, 'backgrounds')
# # #                self.categories.append('backgrounds')
# #
# # #        det_intercals = self._get_detector_intercalibrations()
# # #        if det_intercals:
# # # #            self.categories.insert(-1, 'Det. Intercal.')
# # #            self.categories.append('Det. Intercal.')
#
#     def get_baseline_corrected_signal_dict(self):
#         d = dict()
#         for ki in ['Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36']:
#             if self.isotopes.has_key(ki):
#                 v = self.isotopes[ki].baseline_corrected_value()
#             else:
#                 v = ufloat(0, 0)
#
#             d[ki] = v
#
#         return d
#
#     def get_corrected_value(self, key):
#         return self.isotopes[key].get_corrected_value()
# #===============================================================================
# # handlers
# #===============================================================================
#
# #===============================================================================
# # private
# #===============================================================================
#
#     def _apply_history_change(self, new):
#         self.changed = True
#
#     def _unpack_blob(self, blob, endianness='>'):
#         return zip(*[struct.unpack('{}ff'.format(endianness), blob[i:i + 8]) for i in xrange(0, len(blob), 8)])
#
#     def _make_stacked_graph(self, kind, regress=True):
#         if regress:
#             klass = StackedRegressionGraph
#         else:
#             klass = StackedGraph
#
#         graph = self._graph_factory(klass, width=self.item_width)
#         gkw = dict(padding=[50, 50, 5, 50],
#                    fill_padding=True
#                    )
#
#
#         isos = reversed(self.isotope_keys)
# #        i = 0
#         mi = 10000
#         for i, iso in enumerate(isos):
#             isotope = self.isotopes[iso]
#             if kind == 'baseline':
#                 isotope = isotope.baseline
#
# #            xs, ys = isotope.xs, isotope.ys
#             gkw.update({'ytitle':'{} ({})'.format(isotope.detector, iso),
#                         'xtitle':'Time (s)',
#                         'detector':isotope.detector, 'isotope':iso})
#             graph.new_plot(**gkw)
#
#             fo_dict = dict(filter_outliers=isotope.filter_outliers,
#                              filter_outlier_iterations=isotope.filter_outlier_iterations,
#                              filter_outlier_std_devs=isotope.filter_outlier_std_devs)
#
#             if kind == 'signal':
#                 if isotope.sniff:
#                     mi = min(isotope.sniff.xs[0], mi)
#                     graph.new_series(isotope.sniff.xs,
#                                      isotope.sniff.ys, plotid=i,
#                                      label='sniff',
#                                      fit=False,
#                                      type='scatter',
#                                      marker='circle',
#                                      marker_size=1
#                                      )
#                     graph.set_series_label('sniff', plotid=i)
#
#             mi = min(isotope.xs[0], mi)
#             graph.new_series(isotope.xs, isotope.ys, plotid=i,
#                              type='scatter',
#                              marker='circle',
#                              marker_size=1.25,
#                              filter_outliers_dict=fo_dict,
#                              fit=isotope.fit if regress else False
#                              )
#
#         graph.set_x_limits(min_=mi)
#
#         graph.refresh()
#
#         return graph
#
#     def _make_peak_center_graph(self, xs, ys, center_dac, pcdacs, pcsignals):
#
#         graph = self._graph_factory(width=700)
#         graph.container_dict = dict(padding=[10, 0, 30, 10])
#         graph.clear()
#
#         graph.new_plot(title='Center= {:0.8f}'.format(center_dac),
#                        xtitle='DAC (V)',
#                        ytitle='Intensity (fA)',
#                        )
#
#         scatter, p = graph.new_series(
#                          x=xs, y=ys,
#                          type='scatter', marker='circle',
#                          marker_size=1.25
#                          )
#         graph.new_series(
#                          x=pcdacs,
#                          y=pcsignals,
#                          type='scatter', marker='circle',
#                          marker_size=2
#                          )
#
#         graph.add_point_inspector(scatter)
#
#         graph.add_vertical_rule(center_dac)
#
# #        graph.plots[0].value_range.tight_bounds = False
#         if xs:
#             graph.set_x_limits(min_=min(xs), max_=max(xs))
#         return graph
# #===============================================================================
# # getters
# #===============================================================================
#     def _get_history_item(self, name):
#         '''
#             get the selected history item if available else use the last history
#         '''
#         dbr = self.dbrecord
#         histories = getattr(dbr, '{}_histories'.format(name))
#         if histories:
# #             hist = None
# #             shists = dbr.selected_histories[-1]
# #             if shists:
# #                 hist = getattr(shists, 'selected_{}'.format(name))
#
# #             if hist is None:
# #                 hist = histories[-1]
#
#             hist = dbr.selected_histories
# #             print hist, 'selected_{}'.format(name)
#             hist = getattr(hist, 'selected_{}'.format(name))
#             return getattr(hist, name)
# #             print hist
#
# #             return getattr(hist, name)
#
#     def _get_detector_intercalibrations(self):
#         ds = self.dbrecord.detector_intercalibration_histories
#         return ds
#
#     def _get_blanks(self):
#         bhs = self.dbrecord.blanks_histories
#         return bhs
#
#     def _get_backgrounds(self):
#         bhs = self._dbrecord.backgrounds_histories
#         return bhs
#
#     def _get_peakcenter(self):
#         pc = self._dbrecord.peak_center
#         if pc:
#             x, y = self._unpack_blob(pc.points, endianness='<')
#             center = pc.center
# #            self.peak_center_dac = center
#             return x, y, center, [], []
#
#     def _get_db_fit(self, name, kind):
#         record = self.dbrecord
#
#         try:
#             selhist = record.selected_histories
#             selfithist = selhist.selected_fits
#             fits = selfithist.fits
#             return next((fi for fi in fits
#                                 if fi.isotope.kind == kind and \
#                                     fi.isotope.molecular_weight.name == name
#                                     ), None)
#
#
#         except AttributeError:
#             pass
# #         if selhist:
# #             selfithist = selhist.selected_fits
# #             if selfithist:
# #                 fits = selfithist.fits
# #                 return next((fi for fi in fits
# #                                 if fi.isotope.molecular_weight.name == name and
# #                                 fi.isotope.kind == kind), None)
# #===============================================================================
# # property get/set
# #===============================================================================
#
#     @cached_property
#     def _get_irradiation(self):
#         try:
#             lev = self.irradiation_level
#             return lev.irradiation
#         except AttributeError:
#             pass
#
#     def _get_discrimination(self):
#         disc = ufloat(1, 0)
#         name = 'detector_param'
#         item = self._get_history_item(name)
#         if item:
#             disc = ufloat(item.disc, item.disc_error)
#         return disc
#
#     def get_ic_factor(self, det):
#         r = 1, 0
#         if self.dbrecord.selected_histories:
#             hist = self.dbrecord.selected_histories.selected_detector_intercalibration
#             if hist:
#                 icf = next((ic for ic in hist.detector_intercalibrations
#                             if ic.detector.name == det), None)
#                 if icf:
#                     r = icf.user_value, icf.user_error
#
#         return r
#
#
# #     @cached_property
# #     def _get_ic_factor(self):
# #         ic = ufloat(1.0, 0)
# #         name = 'detector_intercalibration'
# #         items = self._get_history_item(name)
# # #        print items
# #         if items:
# #
# #             '''
# #                 only get the cdd ic factor for now
# #                 its the only one with non unity
# #             '''
# #
# #             # get Ar36 detector
# #             det = next((iso.detector for iso in self.dbrecord.isotopes
# #                       if iso.molecular_weight.name == 'Ar36'), None)
# # #            for iso in self.dbrecord.isotopes:
# # #                print iso
# #             if det:
# #
# #                 # get the intercalibration for this detector
# #                 item = next((item for item in items if item.detector == det), None)
# #                 ic = ufloat(item.user_value, item.user_error)
# #
# # #                if not item.fit:
# # #    #                s = Value(value=item.user_value, error=item.user_error)
# # #                    ic = item.user_value, item.user_error
# # #                else:
# # #                    intercal = lambda x:self._intercalibration_factory(x, 'Ar40', 'Ar36', 295.5)
# # #                    data = map(intercal, item.sets)
# # #                    xs, ys, es = zip(*data)
# # #
# # #                    s = InterpolatedRatio(timestamp=self.timestamp,
# # #                                          fit=item.fit,
# # #                                          xs=xs, ys=ys, es=es
# # #                                          )
# # #                    ic = s.value, s.error
# #
# #         return ic
#
#     @cached_property
#     def _get_record_id(self):
#         return make_runid(self.labnumber, self.aliquot, self.step)
#
# #     @cached_property
# #     def _get_labnumber_record(self):
# #         return self.dbrecord.labnumber
#     def _get_irradiation_level(self):
#         return self.dbrecord.labnumber.irradiation_position.level
#
#     @cached_property
#     def _get_irradiation_position(self):
#         try:
#             return self.dbrecord.labnumber.irradiation_position
#         except AttributeError, e:
#             print 'pos2', e
#
#     @cached_property
#     def _get_labnumber(self):
#         if self._dbrecord:
#             if self._dbrecord.labnumber:
#                 ln = self._dbrecord.labnumber.identifier
#                 return ln
#
#     @cached_property
#     def _get_shortname(self):
#         if self._dbrecord:
#             ln = self._dbrecord.labnumber.identifier
#             return make_runid(ln, self.aliquot, self.step)
#
#     @cached_property
#     def _get_analysis_type(self):
#         try:
#             return self._dbrecord.measurement.analysis_type.name
#         except AttributeError:
#             self.debug('no analysis type')
#
#     @cached_property
#     def _get_mass_spectrometer(self):
#         try:
#             return self._dbrecord.measurement.mass_spectrometer.name.lower()
#         except AttributeError:
#             self.debug('no mass spectrometer')
#
#     @cached_property
#     def _get_isotope_keys(self):
#
# #         self.load_isotopes()
#         keys = self.isotopes.keys()
#         return sort_isotopes(keys)
#
#     @cached_property
#     def _get_isotope_fits(self):
#         keys = self.isotope_keys
#         fs = [self.isotopes[ki].fit
#                     for ki in keys]
# #         fits = [iso.fit for iso in self.isotopes.itervalues()]
# #         z = zip(keys, fits)
# #         zs = sort_isotopes(z)
# #         _ks, fs = zip(*zs)
#         return fs
#
# #===============================================================================
# # dbrecord values
# #===============================================================================
#     def _get_j(self):
#         s = 1.0
#         e = 1e-3
#
#         try:
#             f = self.dbrecord.labnumber.selected_flux_history.flux
#             s = f.j
#             e = f.j_err
#         except AttributeError:
#             pass
#
#         return ufloat(s, e, 'j')
#
#     @cached_property
#     def _get_timestamp(self):
#         analysis = self.dbrecord
#         analts = analysis.analysis_timestamp
#         return time.mktime(analts.timetuple())
#
#     @cached_property
#     def _get_rundate(self):
#         dbr = self.dbrecord
#         if dbr and dbr.analysis_timestamp:
#             date = dbr.analysis_timestamp.date()
#             return date.strftime('%Y-%m-%d')
#
#     @cached_property
#     def _get_runtime(self):
#         dbr = self.dbrecord
#         if dbr and dbr.analysis_timestamp:
#             ti = dbr.analysis_timestamp.time()
#             return ti.strftime('%H:%M:%S')
#
#     @cached_property
#     def _get_sample(self):
#         r = ''
#         dbr = self.dbrecord
#         ln = dbr.labnumber
#         if ln.sample:
#             r = ln.sample.name
#
#         return r
#
#     @cached_property
#     def _get_material(self):
#         m = ''
#         dbr = self.dbrecord
#         ln = dbr.labnumber
#         if ln.sample and ln.sample.material:
#             m = ln.sample.material.name
#         return m
#
#     @cached_property
#     def _get_project(self):
#         ln = self.dbrecord.labnumber
#         sample = ln.sample
#         return sample.project.name
#
#     @cached_property
#     def _get_sensitivity(self):
#         def func(dbr):
#             if dbr.extraction:
#                 if dbr.extraction.sensitivity:
#                     return dbr.extraction.sensitivity.sensitivity
#
#         return self._get_dbrecord_value('sensitivity', func=func, default=1)
#
#     @cached_property
#     def _get_sensitivity_multiplier(self):
#         def func(dbr):
#             if dbr.extraction:
#                 return dbr.extraction.sensitivity_multiplier
#         return self._get_dbrecord_value('sensitivity_multiplier', func=func, default=1)
#
#
#     def _get_aliquot(self):
#         return self._get_dbrecord_value('aliquot', default=0)
#
#     def _get_step(self):
#         return self._get_dbrecord_value('step', default='')
#
#     @property
#     def aliquot_step_str(self):
#         return '{:02n}{}'.format(self.aliquot, self.step)
# #===============================================================================
# # extraction
# #===============================================================================
#     def _get_extraction_value(self, attr, func=None, *args, **kw):
#         '''
#             r = NULL_STR
#             dbr = self._dbrecord
#             if dbr.extraction:
#                 r = dbr.extraction.position
#             return r
#         '''
#         r = NULL_STR
#         dbr = self._dbrecord
#         if dbr.extraction:
#             if func is None:
#                 r = getattr(dbr.extraction, attr)
#             else:
#                 r = func(dbr.extraction)
#         return r
#
#     def _get_position(self):
#         r = NULL_STR
#         pos = self._get_extraction_value('positions')
#         if pos == NULL_STR:
#             return NULL_STR
#
#         pp = []
#         for pi in pos:
#             pii = pi.position
#
#             if pii:
#                 pp.append(pii)
#             else:
#                 ppp = []
#                 x, y, z = pi.x, pi.y, pi.z
#                 if x is not None and y is not None:
#                     ppp.append(x)
#                     ppp.append(y)
#                 if z is not None:
#                     ppp.append(z)
#
#                 if ppp:
#                     pp.append('({})'.format(','.join(ppp)))
#
#         if pp:
#             r = ','.join(map(str, pp))
#
#         return r
#
#     def _get_extract_device(self):
#         def get(ex):
#             r = NULL_STR
#             if ex.extraction_device:
#                 r = ex.extraction_device.name
#             return r
#
#         return self._get_extraction_value(None, func=get)
#
#     def _get_extract_units(self):
#         return 'W'
#
#     def _get_peak_center_dac(self):
#         pc = self._get_peakcenter()
#         if pc:
#             return pc.center
#         else:
#             return 0
#
#     def _get_status(self):
#         return self._get_dbrecord_value('status')
#
#     def _get_dbrecord(self):
#         return self._dbrecord
#
# #    def _get_extract_value(self):
# #        return self._get_extraction_value('extract_value')
# #    def _get_extract_duration(self):
# #        return self._get_extraction_value('extract_duration')
# #    def _get_cleanup_duration(self):
# #        return self._get_extraction_value('cleanup_duration')
# #    def _get_experiment(self):
# #        return self._get_dbrecord_value('experiment')
# #    def _get_extraction(self):
# #        return self._get_dbrecord_value('extraction')
# #    def _get_measurement(self):
# #        return self._get_dbrecord_value('measurement')
# #    @cached_property
# #    def _get_uuid(self):
# #        return self._get_dbrecord_value('uuid')
# #    @cached_property
# #    def _get_aliquot(self):
# #        return self._get_dbrecord_value('aliquot')
# #    def _get_comment(self):
# #        return self._get_dbrecord_value('comment')
# #    @cached_property
# #    def _get_step(self):
# #        return self._get_dbrecord_value('step')
#
#
#     DB_ATTRS = {
#               'experiment':(None, None, None),
#               'extraction':(None, None, None),
#               'uuid':(None, None, None),
#               'comment':(None, None, None),
#               'aliquot':(None, None, None),
#               'step':(None, None, None),
#               'status':(None, None, None),
#               'extract_value':('_get_extraction_value', None, None),
#               'extract_duration':('_get_extraction_value', None, None),
#               'cleanup_duration':('_get_extraction_value', None, None),
#               }
#
#     def __getattr__(self, attr):
#         if attr in self.DB_ATTRS:
#             getter, func, default = self.DB_ATTRS[attr]
#
#             if getter is None:
#                 getter = '_get_dbrecord_value'
#
#             getter = getattr(self, getter)
#             return getter(attr, func, default)
#
#     def _get_dbrecord_value(self, attr, func=None, default=None):
#         v = None
#         if self._dbrecord:
#             if func is not None:
#                 v = func(self._dbrecord)
#             else:
#                 v = getattr(self._dbrecord, attr)
#
#         if v is None:
#             v = default
#         return v
# #===============================================================================
# # defaults
# #===============================================================================
# #     def _analysis_summary_default(self):
# # #         fs = FitSelector(analysis=self,
# # #                          name='Signal'
# # #                          )
# #         item = AnalysisSummary(record=self,
# # #                                fit_selector=fs
# #                                )
# # #         fs.on_trait_change(item.refresh, 'fits:[fit,filterstr,filter_outliers]')
# #         return item
#
#     def _peak_center_graph_default(self):
#         peakcenter = self._get_peakcenter()
#         if peakcenter:
#             return self._make_peak_center_graph(*peakcenter)
#
# #     def _baseline_graph_default(self):
# #         g = self._make_stacked_graph('baseline')
# #            g.refresh()
# #         baseline_graph = EditableGraph(graph=g, fit_selector=self.analysis_summary.fit_selector)
# #         baseline_graph.fit_selector = FitSelector(analysis=self,
# #                                                     kind='baseline',
# #                                                     name='Baseline',
# #                                                     graph=baseline_graph)
# #
# #         baseline_graph.fit_selector.refresh()
# #         return baseline_graph
# #         return g
#
# #     def _signal_graph_default(self):
# #         g = self._make_stacked_graph('signal')
# #         return g
# #         fs = self.analysis_summary.fit_selector
# #         signal_graph = EditableGraph(graph=g, fit_selector=self.analysis_summary.fit_selector)
# #         fs.graph = signal_graph
#
# #         fs.refresh()
# #         return signal_graph
#============= EOF =============================================

#    def _selected_changed(self):
#        selected = self.selected
#        if selected is not None:
#
#            selected = selected.replace(' ', '_')
#            selected = selected.lower()
#
#            self.debug('selected= {}'.format(selected))
#            if selected in (
#                            'blanks',
#                            'backgrounds',
#                            'det._intercal.',
#                            'irradiation',
#                            'supplemental',
#                            'measurement',
#                            'extraction', 'experiment', 'notes',
#                            'error',
#                            ):
#                item = getattr(self, '{}_summary'.format(selected))
#            elif selected == 'summary':
#                item = self.analysis_summary
# #            elif selected == 'blanks':
# #                item = self.blanks_summary  # BlanksSummary(record=self)
# #            elif selected == 'backgrounds':
# #                item = self.backgrounds_summary
# #            elif selected == 'det._intercal.':
# #                item = self.detector_intercalibration_summary
# #            elif selected == 'irradiation':
# #                item = self.irradiation_summary
# #            elif selected == 'supplemental':
# #                item = self.supplemental_summary
# #            elif selected == 'measurement':
# #                item = self.measurement_summary
# #            elif selected == 'extraction':
# #                item = self.extraction_summary
# #            elif selected == 'experiment':
# #                item = self.experiment_summary
# #            elif selected == 'notes':
# #                item = self.notes_summary
#            else:
#                name = '{}_graph'.format(selected)
#                item = getattr(self, name)
#
#            self.display_item = item
#            if hasattr(item, 'refresh'):
#                item.refresh()

#    def _load_histories(self):
#
#        #load blanks
#        self._load_from_history('blanks', Blank)
#
#        #load backgrounds
#        self._load_from_history('backgrounds', Background)
#
# #        #load airs for detector intercal
# #        self._load_detector_intercalibration()
# #
# #    def _load_detector_intercalibration(self):
# #        pass
#
#    def _load_from_history(self, name, klass, **kw):
#        kind = name[:-1]
#        item = self._get_history_item(name)
#        if item:
#            for bi in item:
#                isotope = bi.isotope
#                iso = self.isotopes[isotope.name]
#                nitem = klass(bi, None)
#
#                nitem._value = bi.user_value if bi.user_value else 0
#                nitem._error = bi.user_error if bi.user_error else 0
#                nitem.fit = bi.fit
#
#                setattr(iso, kind, nitem)
#                if kind == 'blank':
#                    iso.b = nitem

#                if not bi.fit:
# #                if not bi.use_set:
#                    s = klass(timestamp=self.timestamp, **kw)
#                    s.value = bi.user_value
#                    s.error = bi.user_error
#                else:
#                    xs, ys, es = zip(*[(ba.timestamp,
#                                        ba.signals[isotope].value,
#                                        ba.signals[isotope].error)
#                                   for ba in map(self._record_factory, bi.sets)])
#                    xs = []
#                    ys = []
#                    for ba in bi.sets:
#                        bb = self.__class__(_dbrecord=ba.analysis)
#                        a = bb.timestamp
#                        b = bb.signals[isotope].value
#                        xs.append(a)
#                        ys.append(b)

#                    s = klass(timestamp=self.timestamp,
#                              xs=xs, ys=ys, es=es,
#                              fit=bi.fit.lower(),
#                              **kw)
#                    print 'ssss', s
#                    s.xs = xs
#                    s.ys = ys
#                    s.es = es
#                    s.fit = bi.fit.lower()
#                print isotope, key
#                self._signals['{}{}'.format(isotope, key)] = s

#    def _make_signal_graph(self, refresh=True):
#        graph = self.signal_graph
#        if graph is None:
#            g = self._make_stacked_graph('signal')
# #            g.refresh()
#            fs = self.analysis_summary.fit_selector
#            self.signal_graph = EditableGraph(graph=g, fit_selector=self.analysis_summary.fit_selector)
#            fs.graph = self.signal_graph
#            if refresh:
#                fs.refresh()
# #
#    def _make_baseline_graph(self):
#        graph = self.baseline_graph
#        if graph is None:
#            g = self._make_stacked_graph('baseline')
# #            g.refresh()
#            self.baseline_graph = EditableGraph(graph=g, fit_selector=self.analysis_summary.fit_selector)
#            self.baseline_graph.fit_selector = FitSelector(analysis=self,
#                                                        kind='baseline',
#                                                        name='Baseline',
#                                                        graph=self.baseline_graph)
#
#            self.baseline_graph.fit_selector.refresh()
#===============================================================================
# factories
#===============================================================================

#===============================================================================
# views
#===============================================================================
#    def traits_view(self):
#        grp = HSplit(
#                        Item('categories', editor=ListStrEditor(
#                                                                editable=False,
#                                                                operations=[],
#                                                                selected='selected'
#                                                                ),
#                             show_label=False,
#                             width=100
#                             ),
#                        Item('display_item', show_label=False, style='custom'),
#                        )
#
#        return self._view_factory(grp)

#    def _load_regressors(self, data):
#        isos = [vi[1] for vi in data.itervalues()]
#        isos = sorted(isos, key=lambda x:re.sub('\D', '', x))
#        def get_data(k):
#            try:
#                return data[k]
#            except KeyError:
#                return next((di for di in data.itervalues() if di[1] == k), None)
#
#        regs = dict()
#        for iso in isos:
#            try:
#                _di, _iso, ofit, (x, y) = get_data(iso)
#            except ValueError:
#                continue
#
#            fit = self._get_iso_fit(iso, ofit)
#
#            x = array(x)
#            y = array(y)
#
# #            if iso == 'Ar40':
# #                import numpy as np
# #                p = '/Users/ross/Sandbox/61311-36b'
# #                xs, ys = np.loadtxt(p, unpack=True)
# #                for ya, yb in zip(ys, y):
# #                    print ya, yb, ya - yb
#
#
# #            exc = RegressionGraph._apply_filter_outliers(x, y)
# #            x = delete(x[:], exc, 0)
# #            y = delete(y[:], exc, 0)
#
#            low = min(x)
#
#            fit = RegressionGraph._convert_fit(fit)
#            if fit in [1, 2, 3]:
#                if len(y) < fit + 1:
#                    return
#                st = low
#                xn = x - st
# #                print x[0], x[-1]
#                r = PolynomialRegressor(xs=xn, ys=y,
#                                        degree=fit)
#                t_fx, t_fy = x[:], y[:]
#                niterations = 1
#                for ni in range(niterations):
#                    excludes = list(r.calculate_outliers())
#                    t_fx = delete(t_fx, excludes, 0)
#                    t_fy = delete(t_fy, excludes, 0)
#                    r = PolynomialRegressor(xs=t_fx, ys=t_fy,
#                                    degree=fit)
#
#            else:
#                r = MeanRegressor(xs=x, ys=y)
#
#            regs[iso] = r
#
#        return regs
