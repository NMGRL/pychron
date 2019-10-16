#!Measurement
'''
baseline:
  after: true
  before: false
  counts: 120
  detector: H1
  mass: 34.2
  settling_time: 15.0
default_fits: nominal
equilibration:
  eqtime: 0.0
  inlet: R
  inlet_delay: 3
  outlet: O
  use_extraction_eqtime: true
multicollect:
  counts: 0
  detector: H1
  isotope: Ar40
peakcenter:
  after: true
  before: false
  detector: H1
  detectors:
  - H1
  - AX
  - CDD
  isotope: Ar40
peakhop:
  hops_name: multihops
  use_peak_hop: true
'''

ACTIVE_DETECTORS=('H2','H1','AX','L1','L2','CDD')
NCYCLES=2

def main():
    info('unknown measurement script')

    activate_detectors(*ACTIVE_DETECTORS)

    if mx.peakcenter.before:
        peak_center(detector=mx.peakcenter.detector,isotope=mx.peakcenter.isotope)

    position_magnet(mx.multicollect.isotope, detector=mx.multicollect.detector)


    '''
    Equilibrate is non-blocking so use a sniff or sleep as a placeholder
    e.g sniff(<equilibration_time>) or sleep(<equilibration_time>)
    '''
    if mx.equilibration.use_extraction_eqtime:
        eqt = eqtime
    else:
        eqt = mx.equilibration.eqtime

    equilibrate(eqtime=eqt, inlet=mx.equilibration.inlet, outlet=mx.equilibration.outlet,
                delay=mx.equilibration.inlet_delay)
    set_time_zero(0)

    # sniff the gas during equilibration
    sniff(eqt)

    hops=load_hops('hops/{}.txt'.format(mx.peakhop.hops_name))
    define_hops(hops)

    set_fits()
    set_baseline_fits()

    if mx.baseline.before:
        baselines(ncounts=mx.baseline.counts,mass=mx.baseline.mass, detector=mx.baseline.detector,
                  settling_time=mx.baseline.settling_time)

    # multicollect on active detectors
    # multicollect(ncounts=MULTICOLLECT_COUNTS, integration_time=1)

    peak_hop(ncycles=NCYCLES, hops=hops)

    if mx.baseline.after:
        # necessary if peak hopping
        define_detectors('Ar40','H1')

        baselines(ncounts=mx.baseline.counts,mass=mx.baseline.mass, detector=mx.baseline.detector,
                  settling_time=mx.baseline.settling_time)

    if mx.peakcenter.after:
        activate_detectors(*mx.peakcenter.detectors, **{'peak_center':True})
        peak_center(detector=mx.peakcenter.detector, isotope=mx.peakcenter.isotope)

    if use_cdd_warming:
       gosub('warm_cdd', argv=(mx.equilibration.outlet,))

    info('finished measure script')
