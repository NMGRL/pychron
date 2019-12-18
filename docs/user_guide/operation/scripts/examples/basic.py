#!Measurement


# all of this is configuration info that can be used in the script.
# you refer to these values using mx.<group>.<attribute>
# e.g
#   mx.baseline.counts is 180
#   mx.multicollect.detector is H1

'''
baseline:
  after: true
  before: false
  counts: 180
  detector: H1
  mass: 34.2
  settling_time: 15
default_fits: nominal
equilibration:
  eqtime: 1.0
  inlet: R
  inlet_delay: 3
  outlet: O
  use_extraction_eqtime: true
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
  isotope: Ar40
peakhop:
  hops_name: ''
  use_peak_hop: false
'''


# entry point for the script

def main():
    # print a message to the user
    info('unknown measurement script')

    # activate the following detectors. measurements will be plotted and save for these detectors
    activate_detectors('H2', 'H1', 'AX', 'L1', 'L2', 'CDD')

    # position the magnet with Ar40 on H1
    position_magnet(mx.multicollect.isotope, detector=mx.multicollect.detector)

    # choose where to get the equilibration duration from
    # sniff the gas during equilibration
    if mx.equilibration.use_extraction_eqtime:
        eqt = eqtime
    else:
        eqt = mx.equilibration.eqtime
    '''
    Equilibrate is non-blocking so use a sniff or sleep as a placeholder
    e.g sniff(<equilibration_time>) or sleep(<equilibration_time>)
    '''
    # start the equilibration thread
    equilibrate(eqtime=eqt, inlet=mx.equilibration.inlet, outlet=mx.equilibration.outlet,
                delay=mx.equilibration.inlet_delay)

    # set time zero after equilibrate returns i.e after the ion pump valve closes
    set_time_zero()

    # record/plot the equilibration
    sniff(eqt)

    # set the default fits
    set_fits()
    set_baseline_fits()

    # multicollect on active detectors for 400
    multicollect(ncounts=mx.multicollect.counts)

    if mx.baseline.after:
        # do a baseline measurement
        baselines(ncounts=mx.baseline.counts, mass=mx.baseline.mass, detector=mx.baseline.detector,
                  settling_time=mx.baseline.settling_time)

    if mx.peakcenter.after:
        # do a peak center scan and update the mftable with new peak centers
        activate_detectors(*mx.peakcenter.detectors, **{'peak_center': True})
        peak_center(detector=mx.peakcenter.detector, isotope=mx.peakcenter.isotope)

    # print a message to the user
    info('finished measure script')