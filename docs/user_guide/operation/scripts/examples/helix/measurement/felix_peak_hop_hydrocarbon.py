#!Measurement
'''
baseline:
  after: true
  before: false
  counts: 120
  detector: AX(CDD)
  mass: PHHCbs
  use_dac: false
  settling_time: 15.0
  nominal_isotope: Ar40
default_fits: nominal
equilibration:
  eqtime: 0.0
  inlet: H
  inlet_delay: 3
  outlet: V
  use_extraction_eqtime: true
multicollect:
  counts: 0
  detector: H2
  isotope: Ar40
peakcenter:
  after: true
  before: false
  detector: H2
  detectors:
    - H2
  integration_time: 0.524288
  isotope: Ar40
peakhop:
  generate_ic_table: false
  hops_name: argonH.yaml
  ncycles: 10
  use_peak_hop: true
'''

ACTIVE_DETECTORS=('H2','H2(CDD)','H1(CDD)','AX(CDD)','L1(CDD)','L2(CDD)')

def main():
    info('unknown measurement script')
    
    activate_detectors(*ACTIVE_DETECTORS)
   
    if mx.peakcenter.before:
        peak_center(detector=mx.peakcenter.detector,isotope=mx.peakcenter.isotope)

    set_spectrometer_configuration('argon')    
    
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
    
    if mx.baseline.before:
        baselines(ncounts=mx.baseline.counts,mass=mx.baseline.mass, detector=mx.baseline.detector,
                  settling_time=mx.baseline.settling_time)

    if mx.peakhop.use_peak_hop: 
        set_spectrometer_configuration('argonHC')   
        hops=load_hops('hops/{}'.format(mx.peakhop.hops_name))
        define_hops(hops)
        set_fits()
        set_baseline_fits()
        peak_hop(ncycles=mx.peakhop.ncycles, hops=hops)
        
    else:
        set_fits()
        set_baseline_fits()
        # multicollect on active detectors
        multicollect(ncounts=mx.multicollect.counts, integration_time=1)
   
    set_deflection('H2 (CDD)', 0)
    set_deflection('H1 (CDD)', 0)
    set_deflection('AX (CDD)', 0)
    set_deflection('L1 (CDD)', 0)
    set_deflection('L2 (CDD)', 0)
   
    if mx.baseline.after:
        # necessary if peak hopping
        define_detectors(mx.baseline.nominal_isotope,mx.baseline.detector)
        
        baselines(ncounts=mx.baseline.counts,mass=mx.baseline.mass, detector=mx.baseline.detector,
                  use_dac=mx.baseline.use_dac,
                  settling_time=mx.baseline.settling_time)
    
    if mx.peakcenter.after:
        activate_detectors(*mx.peakcenter.detectors, **{'peak_center':True})
        peak_center(detector=mx.peakcenter.detector, isotope=mx.peakcenter.isotope,
                   integration_time=mx.peakcenter.integration_time)
    
    if use_cdd_warming:
       gosub('warm_cdd', argv=(mx.equilibration.outlet,))      
       
    info('finished measure script')