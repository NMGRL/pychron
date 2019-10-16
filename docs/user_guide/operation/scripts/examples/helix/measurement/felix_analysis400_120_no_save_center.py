#!Measurement
'''
baseline:
  after: true
  before: false
  counts: 120
  detector: H2
  mass: 39.862
  settling_time: 15.0
default_fits: nominal
equilibration:
  eqtime: 1.0
  inlet: H
  inlet_delay: 3
  outlet: V
  use_extraction_eqtime: true
multicollect:
  counts: 400
  detector: L2(CDD)
  isotope: Ar36
peakcenter:
  after: true
  before: false
  detector: H2
  detectors:
  - H1
  - L2(CDD)
  isotope: Ar40
  integration_time: 1.048576
peakhop:
  hops_name: ''
  use_peak_hop: false
'''
ACTIVE_DETECTORS=('H2','H1','AX','L1','L2(CDD)')
    
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
    equilibrate(eqtime=eqt, inlet=mx.equilibration.inlet, outlet=mx.equilibration.outlet, 
               delay=mx.equilibration.inlet_delay)
    set_time_zero()
    
    sniff(eqt)    
    set_fits()
    set_baseline_fits()
    
    #multicollect on active detectors
    multicollect(ncounts=mx.multicollect.counts, integration_time=1.048576)
    
    if mx.baseline.after:
        #set_integration_time(4.194)
        baselines(ncounts=mx.baseline.counts,mass=mx.baseline.mass, detector=mx.baseline.detector, 
                  settling_time=mx.baseline.settling_time)
        #set_integration_time(1.049)
        
    if mx.peakcenter.after:
        activate_detectors(*mx.peakcenter.detectors, **{'peak_center':True})
        peak_center(detector=mx.peakcenter.detector,isotope=mx.peakcenter.isotope, 
                    integration_time=mx.peakcenter.integration_time, save=False)

    if use_cdd_warming:
       gosub('warm_cdd', argv=(mx.equilibration.outlet,))    
       
    info('finished measure script')
    