#!Measurement
'''
baseline:
  after: true
  before: false
  counts: 40
  detector: H1
  mass: 34.2
  settling_time: 20.0
default_fits: nominal_linear
equilibration:
  eqtime: 20.0
  inlet: R
  inlet_delay: 3
  outlet: O
  use_extraction_eqtime: true
multicollect:
  counts: 400
  detector: H1
  isotope: Ar40
peakcenter:
  after: false
  before: false
  detector: H1
  detectors:
  - H1
  - AX
  - CDD
  isotope: Ar40
peakhop:
  hops_name: ''
  use_peak_hop: false
whiff:
  eqtime: 4
  counts: 1
  abbreviated_count_ratio: 0.25
  conditionals:
    - action: run_remainder
      teststr: Ar40.cur<=175
      attr: Ar40
    - action: run_pipette
      teststr: Ar40.cur>500
      attr: Ar40
    - action: run_chamber_split
      teststr: Ar40.cur>=300
      attr: Ar40
    - action: pump
      teststr: Ar40.cur>175
      attr: Ar40
'''


ACTIVE_DETECTORS=('H2','H1','AX','L1','L2', 'CDD')
#FITS=('Ar41:linear','Ar40:linear', 'Ar39:linear','Ar38:linear','Ar37:linear','Ar36:linear')

def main():

    info('co2 whiff measurement script')

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

    meqtime = mx.whiff.eqtime
    equil(meqtime, False)

    result = whiff(ncounts=mx.whiff.counts, conditionals=mx.whiff.conditionals)
    info('Whiff result={}'.format(result))
    wab=1.0
    if result=='run_remainder':
        open('R')
        open('S')
        sleep(eqtime)
        close('R')
        post_equilibration()
    elif result == 'run_pipette':
        #matt added post_equilibration
        post_equilibration()
    elif result=='run_chamber_split':
        reset_measurement(ACTIVE_DETECTORS)
        activate_detectors(*ACTIVE_DETECTORS)
        open('R')
        open(mx.equilibration.outlet)
        sleep(8)
        close('R')
        open('S')
        sleep(3)
        close('T')
        sleep(3)

        # pump out microbone
        open('U')
        sleep(15)
        close('U')
        sleep(1)
        open('T')
        equil(eqtime)

    elif result=='pump':
        reset_measurement(ACTIVE_DETECTORS)
        activate_detectors(*ACTIVE_DETECTORS)

        #pump out spectrometer and sniff volume
        open('R')
        open(mx.equilibration.outlet)
        sleep(15)
        #close(mx.equilibration.outlet)

        close('R')
        open('S')
        sleep(3)
        close('T')
        sleep(3)

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
