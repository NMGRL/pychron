#!Measurement
'''
'''
#counts

#baselines
BASELINE_COUNTS= 60
BASELINE_DETECTOR= 'H2'
BASELINE_MASS= 39.85
BASELINE_BEFORE= False
BASELINE_AFTER= True
BASELINE_SETTLING_TIME= 10

#peak center
PEAK_CENTER_BEFORE= False
PEAK_CENTER_AFTER= False
PEAK_CENTER_DETECTOR= 'H2'
PEAK_CENTER_ISOTOPE= 'Ar40'
PEAK_DETECTORS= ('H2','L2(CDD)')

#equilibration
EQ_TIME= eqtime
#EQ_TIME = 1

INLET= 'H'
OUTLET= 'V'
EQ_DELAY= 3.0

ACTIVE_DETECTORS=('H2','H1','L1')
#ACTIVE_DETECTORS=('H2','H1','AX','L1','L2','CDD')
#FITS=('Ar40H1:parabolic','Ar40AX:parabolic','Ar40L1:parabolic','Ar40L2:parabolic')
#FITS=('Ar40H2:parabolic','Ar40H1:parabolic','Ar40AX:parabolic','Ar40L1:parabolic','Ar40L2:parabolic')
FITS = ('Ar40H2:parabolic','Ar40H1:parabolic','Ar40L1:parabolic')
#('Ar41:average_SEM','Ar40:parabolic','Ar39:parabolic','Ar38:linear','Ar37:linear','Ar36:parabolic','Ar35:linear')
BASELINE_FITS=('average_SEM',)
USE_WARM_CDD=False

NCYCLES=6
GENERATE_ICMFTABLE=True

def main():
    info('unknown measurement script')

    activate_detectors(*ACTIVE_DETECTORS)

    #if PEAK_CENTER_BEFORE:
    #    peak_center(detector=PEAK_CENTER_DETECTOR,isotope=PEAK_CENTER_ISOTOPE)

    #set_deflection('L2(CDD)', 3250)

    #position_magnet('Ar40', detector='H1')

    hops=load_hops('hops/ic_hops.txt')
    info(hops)
    define_hops(hops)
    '''
    Equilibrate is non-blocking so use a sniff or sleep as a placeholder
    e.g sniff(<equilibration_time>) or sleep(<equilibration_time>)
    '''
    #equilibrate(eqtime=EQ_TIME, inlet=INLET, outlet=OUTLET, delay=EQ_DELAY)
    set_time_zero()

    #sniff the gas during equilibration
    #sniff(EQ_TIME-1)
    #sleep(EQ_TIME-1)
    set_fits(*FITS)
    set_baseline_fits(*BASELINE_FITS)

    sleep(0.5)

    #if BASELINE_BEFORE:
    #    baselines(ncounts=BASELINE_COUNTS,mass=BASELINE_MASS, detector=BASELINE_DETECTOR,
    #              settling_time=BASELINE_SETTLING_TIME)

    #multicollect on active detectors
    #multicollect(ncounts=MULTICOLLECT_COUNTS, integration_time=1)
    if GENERATE_ICMFTABLE:
        generate_ic_mftable(('H2','H1','L1'), peak_center_config='ic_peakhop', n=3)
        set_time_zero()

    peak_hop(ncycles=NCYCLES, hops=hops, mftable='ic_mftable')
    #peak_hop(ncycles=NCYCLES, hops=hops, mftable='argon')

    if BASELINE_AFTER:
        #necessary if peak hopping
        define_detectors('Ar40','H2')
        define_detectors('Ar39','H1')
        define_detectors('Ar37','L1')

        baselines(ncounts=BASELINE_COUNTS,mass=BASELINE_MASS, detector=BASELINE_DETECTOR,
                  settling_time=BASELINE_SETTLING_TIME)
    if PEAK_CENTER_AFTER:
        activate_detectors(*PEAK_DETECTORS, **{'peak_center':True})
        peak_center(detector=PEAK_CENTER_DETECTOR, isotope=PEAK_CENTER_ISOTOPE)

    if USE_WARM_CDD:
       gosub('warm_cdd', argv=(OUTLET,))

    #set_deflection('L2(CDD)', 0)

    info('finished measure script')
