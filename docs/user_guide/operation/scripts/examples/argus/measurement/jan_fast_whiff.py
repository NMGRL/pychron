#!Measurement
'''
baseline:
  after: true
  before: false
  counts: 30
  detector: H1
  mass: 39.59
default_fits: nominal
multicollect:
  counts: 60
  detector: H1
  isotope: Ar40
peakcenter:
  after: false
  before: false
  detector: H1
  isotope: Ar40
equilibration:
  inlet: R
  outlet: O
  inlet_delay: 3
  eqtime: 20
  use_extraction_eqtime: True
whiff:
  split_A_valve: L
  counts: 4
  abbreviated_count_ratio: 1.0
  conditionals:
    - action: run_total
      attr: Ar40
      teststr: Ar40.cur<50
    - action: run
      attr: Ar40
      teststr: Ar40.cur<100
    - action: run_split
      teststr: Ar40.cur>100
      attr: Ar40
'''

ACTIVE_DETECTORS=('H2','H1','AX','L1','L2', 'CDD')
#FITS=('Ar41:linear','Ar40:linear', 'Ar39:parabolic','Ar38:parabolic','Ar37:parabolic','Ar36:parabolic')

def main():
    """
        This script does a fast whiff measurement
        0. Split analytical section
        1. close ion pump
        2. wait 2 seconds
        3. open inlet
        4. do whiff for 4 seconds
        5. make decision
        
        run: Finish equilibration and run gas
        run_total: run split_A and split_B together
        run_split: pump out mass spec and split gas. 
                   isolate co2 chamber, pump out microbone, expand co2 chamber
    """
    info('Fast Whiff script')
    
    # peak center before
    if mx.peakcenter.before:
        peak_center(detector=mx.peakcenter.detector,isotope=mx.peakcenter.isotope)

    # setup
    # open a plot panel for this detectors
    activate_detectors(*ACTIVE_DETECTORS)
    
    # baseline before
    if mx.baseline.before:
        baselines(ncounts=mx.baseline.counts,mass=mx.baseline.mass, detector=mx.baseline.detector)
        
    # position mass spectrometer for normal analysis
    position_magnet(mx.multicollect.isotope, detector=mx.multicollect.detector)

    # isolate split A
    close(mx.whiff.split_A_valve)
    # equilibrate
    set_time_zero()
    close(mx.equilibration.outlet)
    sleep(2)
    open(mx.equilibration.inlet)
    
    # do fast whiff
    result = whiff(ncounts=mx.whiff.counts, conditionals=mx.whiff.conditionals)
    info('Whiff result={}'.format(result))
    wab=1.0
    if result=='run':
        info('Continuing whiff measurment')
        # finish equilibration
        sleep(10)
        close(mx.equilibration.inlet)       
        post_equilibration()
        wab = mx.whiff.abbreviated_count_ratio
    elif result=='run_total':
        #reset_measurement(ACTIVE_DETECTORS)
        info('Run total')
        open(mx.whiff.split_A_valve)
        sleep(10)
        close(mx.equilibration.inlet)  
        set_fits()
        set_baseline_fits()     
        post_equilibration(block=False)
        wab = mx.whiff.abbreviated_count_ratio
    elif result=='run_split':
       info('Measuring remainder instead')
       reset_measurement(ACTIVE_DETECTORS)
       
       close(mx.equilibration.inlet)
       close(mx.whiff.split_A_valve)
       
       # pump out spectrometer
       open(mx.equilibration.outlet)
       # pump out microbone
       open(description='Microbone to Turbo')
       sleep(15)
       close(description='Microbone to Turbo')   
       
       #equilibrate split
       open(mx.whiff.split_A_valve)
       sleep(5)
       
       #equilibrate with entire section
       equil(eqtime)
        
    multicollect(ncounts=mx.multicollect.counts*wab, integration_time=1)
    if mx.baseline.after:
        baselines(ncounts=mx.baseline.counts*wab, mass=mx.baseline.mass, detector=mx.baseline.detector)

    if mx.peakcenter.after:
        peak_center(detector=mx.peakcenter.detector,isotope=mx.peakcenter.isotope)
    info('finished measure script')

def equil(eqt, do_post=True, set_tz=True):
    #post equilibration script triggered after eqtime elapsed
    #equilibrate is non blocking
    #so use either a sniff of sleep as a placeholder until eq finished
    equilibrate(eqtime=eqt, do_post_equilibration=do_post,
                inlet=mx.equilibration.inlet, 
                outlet=mx.equilibration.outlet)

    #equilibrate returns immediately after the inlet opens
    if set_tz:
        set_time_zero(0)

    sniff(eqt)
    #set default regression
    set_fits()
    set_baseline_fits()
#========================EOF==============================================================

