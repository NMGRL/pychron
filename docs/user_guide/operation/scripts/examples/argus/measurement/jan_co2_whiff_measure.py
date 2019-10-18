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
  eqtime: 10
  counts: 10
  abbreviated_count_ratio: 0.25
  conditionals:
    - action: run
      attr: Ar40
      teststr: Ar40>10
    - action: run_remainder
      teststr: Ar40<=10
      attr: Ar40
'''

ACTIVE_DETECTORS=('H2','H1','AX','L1','L2', 'CDD')
#FITS=('Ar41:linear','Ar40:linear', 'Ar39:parabolic','Ar38:parabolic','Ar37:parabolic','Ar36:parabolic')

def main():
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

    meqtime = mx.whiff.eqtime
    equil(meqtime, False)
    
    
    result = whiff(ncounts=mx.whiff.counts, conditionals=mx.whiff.conditionals)
    info('Whiff result={}'.format(result))
    wab=1.0
    if result=='run':
       info('Continuing whiff measurment')
       post_equilibration()
       wab = mx.whiff.abbreviated_count_ratio
    elif result=='run_remainder':
       info('Measuring remainder instead')
       reset_measurement(ACTIVE_DETECTORS)
       
       #pump out spectrometer
       #open(mx.equilibration.outlet)
       #sleep(15)
       
       #open co2 chamber
       open('T')
       
       #equilibrate with entire section
       equil(eqtime)
       
    multicollect(ncounts=mx.multicollect.counts*wab, integration_time=1)
    if mx.baseline.after:
        baselines(ncounts=mx.baseline.counts*wab, mass=mx.baseline.mass, detector=mx.baseline.detector)

    if mx.peakcenter.after:
        peak_center(detector=mx.peakcenter.detector,isotope=mx.peakcenter.isotope)
    info('finished measure script')

def equil(eqt, do_post=True):
    #post equilibration script triggered after eqtime elapsed
    #equilibrate is non blocking
    #so use either a sniff of sleep as a placeholder until eq finished
    equilibrate(eqtime=eqt, do_post_equilibration=do_post,
                inlet=mx.equilibration.inlet, outlet=mx.equilibration.outlet)

    #equilibrate returns immediately after the inlet opens
    set_time_zero(0)

    sniff(eqt)
    #set default regression
    set_fits()
    set_baseline_fits()
#========================EOF==============================================================
    #peak_hop(detector='CDD', isotopes=['Ar40','Ar39','Ar36'], cycles=2, integrations=3)
    #baselines(counts=50,mass=0.5, detector='CDD')s

#isolate sniffer volume
    # close('S')
#     sleep(1)
#
#     #open to mass spec
#     open('R')
#
#     set_time_zero()
#     #display pressure wave
#     sniff(5)
#
#     #define sniff/split threshold
#     sniff_threshold=100
#
#     #test condition
#     #if get_intensity('H1')>sniff_threshold:
#     if True:
#         gosub('splits:jan_split', klass='ExtractionLinePyScript')
#
