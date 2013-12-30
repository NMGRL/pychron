import math
from copy import deepcopy

from traits.api import HasTraits, Property, List, Button, Str, File, Any
from traitsui.api import View, Item, HGroup, TabularEditor
from uncertainties import ufloat, umath
import xlrd
from traitsui.tabular_adapter import TabularAdapter


def calculate_decay_factor(dc, segments):
    """
        McDougall and Harrison
        p.75 equation 3.22

        the book suggests using ti==analysis_time-end of irradiation segment_i

        mass spec uses ti==analysis_time-start of irradiation segment_i

        using start seems more appropriate
    """

    a = sum([pi * ti for pi, ti, _ in segments])

    b = sum([pi * ((1 - math.exp(-dc * ti)) / (dc * math.exp(dc * dti)))
             for pi, ti, dti in segments])

    return a / b


def calculate_arar_age(signals, baselines, blanks, backgrounds,
                       j, irradinfo,
                       ic=(1.0, 0),
                       abundance_sensitivity=0,
                       a37decayfactor=None,
                       a39decayfactor=None,
                       include_decay_error=False,
                       constants=None
):
    '''
        signals: measured uncorrected isotope intensities, tuple of value,error pairs
            value==intensity, error==error in regression coefficient
        baselines: measured baseline intensity
        !!!
            this method will not work if you want to make a time dependent baseline correction
            mass spec corrects each signal point with a modeled baseline. 
        !!!
        blanks: time dependent background, same format as signals
        background: static spectrometer background, same format as signals
        j: flux, tuple(value,error)
        irradinfo: tuple of production ratios + chronology + decay_time
            production_ratios = k4039, k3839, k3739, ca3937, ca3837, ca3637, cl3638
        
        ic: CDD correction factor
         
         
        return:
            returns a results dictionary with computed values
            result keys
                age_err_wo_j,
                rad40,
                tot40,
                k39,
                ca37,
                atm36,
                cl36,
                
                s40,
                s39,
                s38,
                s37,
                s36,
                ar39decayfactor,
                ar37decayfactor
            
    '''

    def to_ufloat(v):
        if isinstance(v, tuple):
            v = ufloat(v)
        return v

    if constants is None:
        # lazy load constants
        from pychron.processing.constants import Constants

        constants = Constants()

    #    if isinstance(signals[0], tuple):
    s40, s39, s38, s37, s36 = map(to_ufloat, signals)

    #    if isinstance(baselines[0], tuple):
    s40bs, s39bs, s38bs, s37bs, s36bs = map(to_ufloat, baselines)

    #    if isinstance(blanks[0], tuple):
    s40bl, s39bl, s38bl, s37bl, s36bl = map(to_ufloat, blanks)

    #    if isinstance(backgrounds[0], tuple):
    s40bk, s39bk, s38bk, s37bk, s36bk = map(to_ufloat, backgrounds)

    k4039, k3839, k3739, ca3937, ca3837, ca3637, cl3638, chronology_segments, decay_time = irradinfo

    ca3637 = ufloat(ca3637)
    ca3937 = ufloat(ca3937)
    ca3837 = ufloat(ca3837)
    k4039 = ufloat(k4039)
    k3839 = ufloat(k3839)
    cl3638 = ufloat(cl3638)
    k3739 = ufloat(k3739)
    ic = ufloat(ic)
    j = ufloat(j)
    #    temp_ic = ufloat(ic)

    #===============================================================================
    #
    #===============================================================================

    # subtract blanks and baselines (and backgrounds)
    s40 -= (s40bl + s40bs + s40bk)
    s39 -= (s39bl + s39bs + s39bk)
    s38 -= (s38bl + s38bs + s38bk)
    s37 -= (s37bl + s37bs + s37bk)
    s36 -= (s36bl + s36bs + s36bk)

    # apply intercalibration factor to corrected 36
    s36 *= ic

    # correct for abundant sensitivity
    # assumes symmetric and equal abundant sens for all peaks
    n40 = s40 - abundance_sensitivity * (0 + s39)
    n39 = s39 - abundance_sensitivity * (s40 + s38)
    n38 = s38 - abundance_sensitivity * (s39 + s37)
    n37 = s37 - abundance_sensitivity * (s38 + s36)
    n36 = s36 - abundance_sensitivity * (s37 + 0)
    s40, s39, s38, s37, s36 = n40, n39, n38, n37, n36


    # calculate decay factors
    if a37decayfactor is None:
        try:
            dc = constants.lambda_Ar37.nominal_value
            a37decayfactor = calculate_decay_factor(dc, chronology_segments)
        except ZeroDivisionError:
            a37decayfactor = 1

    if a39decayfactor is None:
        try:
            dc = constants.lambda_Ar39.nominal_value
            a39decayfactor = calculate_decay_factor(dc, chronology_segments)
        except ZeroDivisionError:
            a39decayfactor = 1

    # calculate interference corrections
    s37dec_cor = s37 * a37decayfactor
    s39dec_cor = s39 * a39decayfactor

    k37 = ufloat(0, 1e-20)

    # iteratively calculate 37, 39
    for _ in range(5):
        ca37 = s37dec_cor - k37
        ca39 = ca3937 * ca37
        k39 = s39dec_cor - ca39
        k37 = k3739 * k39

    k38 = k3839 * k39
    ca36 = ca3637 * ca37
    ca38 = ca3837 * ca37
    ca39 = ca3937 * ca37

    '''
        McDougall and Harrison
        Roddick 1983
        Foland 1993
        
        iteratively calculate atm36
    '''
    m = cl3638 * constants.lambda_Cl36.nominal_value * decay_time
    atm36 = ufloat(0, 1e-20)
    for _ in range(5):
        ar38atm = constants.atm3836.nominal_value * atm36
        cl38 = s38 - ar38atm - k38 - ca38
        cl36 = cl38 * m
        atm36 = s36 - ca36 - cl36

        # calculate rodiogenic
        # dont include error in 40/36

    #    pc = sc.node('pychron').node('experiment')
    #    print pc
    #    print pc.get('constants')
    #    print pc.node_names()
    atm40 = atm36 * constants.atm4036.nominal_value
    k40 = k39 * k4039
    ar40rad = s40 - atm40 - k40

    age_with_jerr = ufloat(0, 0)
    age_wo_jerr = ufloat(0, 0)
    try:
        R = ar40rad / k39
        # dont include error in decay constant
        age = age_equation(j, R, include_decay_error=include_decay_error, constants=constants)
        #        age = age_equation(j, R)
        age_with_jerr = deepcopy(age)

        # dont include error in decay constant
        j.set_std_dev(0)
        age = age_equation(j, R, include_decay_error=include_decay_error, constants=constants)
        #        age = age_equation(j, R)
        age_wo_jerr = deepcopy(age)

    except (ZeroDivisionError, ValueError), e:
        print e
        age = ufloat(0, 0)
        age_wo_jerr = ufloat(0, 0)

    #    print s40 / s36
    result = dict(
        age=age_with_jerr,
        age_err_wo_j=age_wo_jerr.std_dev,
        rad40=ar40rad,

        k39=k39,
        ca37=ca37,
        atm36=atm36,
        cl36=cl36,

        s40=s40,
        s39=s39,
        s38=s38,
        s37=s37,
        s36=s36,

        s37decay_cor=s37dec_cor,
        s39decay_cor=s39dec_cor,

        ar39decayfactor=a39decayfactor,
        ar37decayfactor=a37decayfactor
    )
    return result


def age_equation(j, R, scalar=1, include_decay_error=False, constants=None):
    if isinstance(j, (tuple, str)):
        j = ufloat(j)
    if isinstance(R, (tuple, str)):
        R = ufloat(R)
    if constants is None:
        from pychron.processing.constants import Constants

        constants = Constants()
    #    print constants.lambda_k, 'dec'
    if include_decay_error:
        age = (1 / constants.lambda_k) * umath.log(1 + j * R) / float(scalar)
    else:
        age = (1 / constants.lambda_k.nominal_value) * umath.log(1 + j * R) / float(scalar)
    return age


class ExcelMixin(object):
    def _make_row(self, sheet, ri, cast=str):
        return [cast(sheet.cell(ri, ci).value) for ci in range(sheet.ncols)]


class Constants(ExcelMixin):
    age_units = 'Ma'

    def __init__(self, sheet):
        self.sheet = sheet
        # lambda_epsilon = ufloat((5.81e-11,
        #                                    0))
        # lambda_beta = ufloat((4.962e-10,
        #                                 0))

        #        lambda_e = ufloat((5.755e-11,
        #                                            1.6e-13))
        #        lambda_b = ufloat((4.9737e-10,
        #                                         9.3e-13))

        lambda_e = self._get_constant('lambda_e', 5.81e-11, 1.6e-13)
        #        lambda_e = get_constant('lambda_e', 5.81e-11, 0)
        lambda_b = self._get_constant('lambda_b', 4.962e-10, 9.3e-13)
        #        lambda_b = get_constant('lambda_b', 4.962e-10, 0)

        self.lambda_k = lambda_e + lambda_b
        # lambda_k = get_constant('lambda_K', 5.81e-11 + 4.962e-10, 0)

        self.lambda_Ar37 = self._get_constant('lambda_Ar37', 0.01975, 0)  # per day
        # lambda_37 = ufloat((0.01975, 0)) #per day
        self.lambda_Ar39 = self._get_constant('lambda_Ar39', 7.068000e-6, 0)  # per day
        # lambda_39 = ufloat((7.068000e-6, 0))  #per day
        self.lambda_Cl36 = self._get_constant('lambda_Cl36', 6.308000e-9, 0)  # per day
        # lambda_cl36 = ufloat((6.308000e-9, 0))  #per day

        # atmospheric ratios
        self.atm4036 = self._get_constant('Ar40_Ar36_atm', 295.5, 0)
        self.atm4038 = self._get_constant('Ar40_Ar38_atm', 1575, 2)

        # atm4038 = ufloat((1575, 2))
        self.atm3638 = self.atm4038 / self.atm4036
        self.atm3836 = self.atm4036 / self.atm4038

    def _get_constant(self, name, value, error):
        sheet = self.sheet
        header = self._make_row(sheet, 0)
        idx = header.index(name)
        idx_err = header.index('{}_err'.format(name))
        try:
            value = sheet.cell(1, idx).value
        except Exception, e:
            print e

        try:
            error = sheet.cell(1, idx_err).value
        except Exception, e:
            print e

        #        print type(value)
        return ufloat(value, error)


# class Isotope(HasTraits):
#    value = Float
#    error = Float
#    uvalue = Property
#    name = Str
#    @cached_property
#    def _get_uvalue(self):
#        return ufloat((self.value, self.error))
#
#    def traits_view(self):
#        v = View(HGroup(Label(self.name), Item('value'), Item('error')))
#        return v

class Result(HasTraits):
    age = Any
    identifier = Str


class ResultAdapter(TabularAdapter):
    columns = [
        ('Identifier', 'identifier'),
        ('Age', 'age'),
        ('Error', 'age_error'),
    ]
    age_text = Property
    age_error_text = Property

    def _float_fmt(self, v, n):
        return '{{:0.{}f}}'.format(n).format(v)

    def _get_value(self, attr):
        v = getattr(self.item, attr)
        return self._float_fmt(v.nominal_value, 5)

    def _get_error(self, attr):
        v = getattr(self.item, attr)
        return self._float_fmt(v.std_dev, 6)

    def _get_age_text(self):
        return self._get_value('age')

    def _get_age_error_text(self):
        return self._get_error('age')


class AgeCalculator(HasTraits, ExcelMixin):
    calc_button = Button
    results = List
    path = File

    def _load_irrad_info_from_file(self, sheet):
        ir_header = self._make_row(sheet, 0)

        idx_k4039 = ir_header.index('k4039')
        idx_k4039err = ir_header.index('k4039_err')
        idx_k3839 = ir_header.index('k3839')
        idx_k3839err = ir_header.index('k3839_err')
        idx_k3739 = ir_header.index('k3839')
        idx_k3739err = ir_header.index('k3839_err')

        idx_ca3937 = ir_header.index('ca3937')
        idx_ca3937err = ir_header.index('ca3937_err')
        idx_ca3837 = ir_header.index('ca3837')
        idx_ca3837err = ir_header.index('ca3837_err')
        idx_ca3637 = ir_header.index('ca3637')
        idx_ca3637err = ir_header.index('ca3637_err')

        idx_cl3638 = ir_header.index('cl3638')
        idx_cl3638err = ir_header.index('cl3638_err')

        row = self._make_row(sheet, 1, cast=float)
        irrad_info = [(row[idx_k4039], row[idx_k4039err]),
                      (row[idx_k3839], row[idx_k3839err]),
                      (row[idx_k3739], row[idx_k3739err]),
                      (row[idx_ca3937], row[idx_ca3937err]),
                      (row[idx_ca3837], row[idx_ca3837err]),
                      (row[idx_ca3637], row[idx_ca3637err]),
                      (row[idx_cl3638], row[idx_cl3638err])
        ]

        return irrad_info + [[], 1]

    def _calc_from_file(self, path):
        self.results = []

        workbook = xlrd.open_workbook(path)
        ir_s = workbook.sheet_by_name('irradiation')
        irrad_info = self._load_irrad_info_from_file(ir_s)

        i_s = workbook.sheet_by_name('intensities')
        header = self._make_row(i_s, 0)

        try:
            bl_s = workbook.sheet_by_name('blanks')
            bl_header = self._make_row(bl_s, 0)
        except xlrd.XLRDError:
            bl_s = None
            bl_header = None
        try:
            bg_s = workbook.sheet_by_name('backgrounds')
            bg_header = self._make_row(bg_s, 0)
        except xlrd.XLRDError:
            bg_header = None
            bg_s = None

        try:
            bs_s = workbook.sheet_by_name('baselines')
            bs_header = self._make_row(bs_s, 0)
        except xlrd.XLRDError:
            bs_header = None
            bs_s = None

        idx_j = header.index('j')
        idx_jerr = header.index('j_err')
        idx_ic = header.index('ic')
        idx_ic_err = header.index('ic_err')

        c_s = workbook.sheet_by_name('constants')
        constants_obj = Constants(c_s)

        for ri in range(1, i_s.nrows):
            signals = self._load_signals(header, i_s, ri)
            blanks = self._load_signals(bl_header, bl_s, ri)
            baselines = self._load_signals(bs_header, bs_s, ri)
            backgrounds = self._load_signals(bg_header, bg_s, ri)

            row = self._make_row(i_s, ri)
            idn = row[0]
            j = map(float, (row[idx_j], row[idx_jerr]))
            ic = map(float, (row[idx_ic], row[idx_ic_err]))
            arar_result = calculate_arar_age(signals, baselines, blanks, backgrounds, j, irrad_info,
                                             a37decayfactor=1, a39decayfactor=1,
                                             ic=ic,
                                             constants=constants_obj)

            self.results.append(Result(identifier=idn,
                                       age=arar_result['age'] / 1e6))

    def _load_signals(self, header, sheet, ri):
        if sheet is not None:
            row = self._make_row(sheet, ri)
            idn = row[0]
            row = [idn] + map(float, row[1:])

            idx_40 = header.index('Ar40')
            idx_40err = header.index('Ar40_err')
            idx_39 = header.index('Ar39')
            idx_39err = header.index('Ar39_err')
            idx_38 = header.index('Ar38')
            idx_38err = header.index('Ar38_err')
            idx_37 = header.index('Ar37')
            idx_37err = header.index('Ar37_err')
            idx_36 = header.index('Ar36')
            idx_36err = header.index('Ar36_err')
            signals = [(row[idx_40], row[idx_40err]),
                       (row[idx_39], row[idx_39err]),
                       (row[idx_38], row[idx_38err]),
                       (row[idx_37], row[idx_37err]),
                       (row[idx_36], row[idx_36err])]

        else:
            signals = [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0)]
        return signals

    def _calc_button_fired(self):
        path = self.path
        self._calc_from_file(path)

    def traits_view(self):
        v = View(
            HGroup(Item('path', springy=True, show_label=False),
                   Item('calc_button', enabled_when='path', show_label=False)),
            Item('results', editor=TabularEditor(adapter=ResultAdapter(),
                                                 editable=False
            ),

                 show_label=False, style='custom'),
            title='Age Calculator',
            width=500,
            height=300,
        )
        return v


if __name__ == '__main__':
    ag = AgeCalculator()
    import os

    p = os.path.join(os.path.dirname(__file__), 'pychron', 'processing', 'data', 'age_calculator_template.xls')
    #    ag.path = '/Users/ross/Sandbox/age_calculator_template.xls'
    ag.path = p
    ag.configure_traits()
