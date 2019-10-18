#!Measurement
'''
baseline:
  after: true
  before: false
  counts: 120
  detector: H1
  mass: 34.2
  settling_time: 15
default_fits: nominal
multicollect:
  counts: 400
  detector: H1
  isotope: Ar40
peakcenter:
  after: true
  before: false
  detector: H1
  isotope: Ar40
  detectors:
   - H1
   - AX
   - CDD
equilibration:
  inlet: R
  outlet: O
  inlet_delay: 3
  eqtime: 20
  use_extraction_eqtime: True
whiff:
  eqtime: 4
  counts: 1
  abbreviated_count_ratio: 0.25
  conditionals:
    - action: run_remainder
      teststr: Ar40.cur<=100
      attr: Ar40
    - action: pump
      teststr: Ar40.cur>100
      attr: Ar40
'''

ACTIVE_DETECTORS=('H2','H1','AX','L1','L2', 'CDD')
#FITS=('Ar41:linear','Ar40:linear', 'Ar39:parabolic','Ar38:parabolic','Ar37:parabolic','Ar36:parabolic')

def main():
    #simulate CO2 analysis
    #open('T')
    #sleep(5)
    
    #close('L')
    #display information with info(msg)
    info('unknown measurement script')

    if mx.peakcenter.before:
        peak_center(detector=mx.peakcenter.detector,isotope=mx.peakcenter.isotope)

    #open a plot panel for this detectors
    activate_detectors(*ACTIVE_DETECTORS)

    if mx.baseline.before:
        baselines(ncounts=mx.baseline.counts,mass=mx.baseline.mass, detector=mx.baseline.detector)

    #position mass spectrometer
    position_magnet(mx.multicollect.isotope, detector=mx.multicollect.detector)

    #gas is staged behind inlet
    
    #make a pipette volume
    close('S')
    sleep(1)
    
    meqtime = mx.whiff.eqtime
    equil(meqtime, False)
    
    result = whiff(ncounts=mx.whiff.counts, conditionals=mx.whiff.conditionals)
    info('Whiff result={}'.format(result))
    wab=1.0
    if result=='run_remainder':
       open('R')
       open('S')
       sleep(eqtime-meqtime)
       close('R')
       post_equilibration()
    elif result=='pump':
        reset_measurement(ACTIVE_DETECTORS)
        activate_detectors(*ACTIVE_DETECTORS)
        
        #pump out spectrometer and sniff volume
        open('R')
        open(mx.equilibration.outlet)
        sleep(15)
        #close(mx.equilibration.outlet)
        
        close('R')
        sleep(1)
        open('S')
        sleep(2)
        close('T')
        sleep(2)
        close(mx.equilibration.outlet)
        
        equil(eqtime)
        
    multicollect(ncounts=mx.multicollect.counts*wab, integration_time=1)
    if mx.baseline.after:
        baselines(ncounts=mx.baseline.counts*wab, mass=mx.baseline.mass, detector=mx.baseline.detector,
        settling_time=mx.baseline.settling_time)

    if mx.peakcenter.after:
        activate_detectors(*mx.peakcenter.detectors, **{'peak_center':True})
        peak_center(detector=mx.peakcenter.detector,isotope=mx.peakcenter.isotope)
    info('finished measure script')

def equil(eqt, do_post=True, set_tzero=True):
    #post equilibration script triggered after eqtime elapsed
    #equilibrate is non blocking
    #so use either a sniff of sleep as a placeholder until eq finished
    equilibrate(eqtime=eqt, do_post_equilibration=do_post,
                inlet=mx.equilibration.inlet, outlet=mx.equilibration.outlet)

    if set_tzero:
        #equilibrate returns immediately after the inlet opens
        set_time_zero(0)

    sniff(eqt)
    #set default regression
    set_fits()
    set_baseline_fits()
#========================EOF==============================================================
