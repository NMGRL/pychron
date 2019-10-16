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
  eqtime: 40
  inlet: R
  inlet_delay: 3
  outlet: O
  use_extraction_eqtime: false
multicollect:
  counts: 400
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
  integration_time: 0.262144
  isotope: Ar40
peakhop:
  generate_ic_table: false
  hops_name: ''
  ncycles: 0
  use_peak_hop: false
'''
ACTIVE_DETECTORS=('H2','H1','AX','L1','L2','CDD')
    
def main():
    info('unknown measurement script')
    
    activate_detectors(*ACTIVE_DETECTORS)
   
    
    if mx.peakcenter.before:
        peak_center(detector=mx.peakcenter.detector,isotope=mx.peakcenter.isotope)
    
    if mx.baseline.before:
        baselines(ncounts=mx.baseline.counts,mass=mx.baseline.mass, detector=mx.baseline.detector,
                  settling_time=mx.baseline.settling_time)
    
    position_magnet(mx.multicollect.isotope, detector=mx.multicollect.detector)

    #sniff the gas during equilibration
    if mx.equilibration.use_extraction_eqtime:
        eqt = eqtime
    else:
        eqt = mx.equilibration.eqtime
    '''
    Equilibrate is non-blocking so use a sniff or sleep as a placeholder
    e.g sniff(<equilibration_time>) or sleep(<equilibration_time>)
    '''
    # turn off HV
    set_deflection("CDD",2000)
    sleep(2)
    set_accelerating_voltage(0)

    equilibrate(eqtime=eqt, inlet=mx.equilibration.inlet, outlet=mx.equilibration.outlet, 
               delay=mx.equilibration.inlet_delay)
    #open('L')

    set_time_zero()
    
    sniff(eqt)    
    set_fits()
    set_baseline_fits()

    # turn on HV
    
    set_accelerating_voltage(4500)
    set_time_zero()
    sleep(8)
    set_deflection("CDD",10)
    sleep(2)
    #multicollect on active detectors
    multicollect(ncounts=mx.multicollect.counts, integration_time=1)
    
    if mx.baseline.after:
        baselines(ncounts=mx.baseline.counts,mass=mx.baseline.mass, detector=mx.baseline.detector, 
                  settling_time=mx.baseline.settling_time)
    if mx.peakcenter.after:
        activate_detectors(*mx.peakcenter.detectors, **{'peak_center':True})
        peak_center(detector=mx.peakcenter.detector,isotope=mx.peakcenter.isotope,
        integration_time=mx.peakcenter.integration_time)

    if True:
       #gosub('warm_cdd', argv=(mx.equilibration.outlet,))    
       gosub('warm_cdd')
       
    info('finished measure script')
    