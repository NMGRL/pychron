Measurement Scripts
---------------------------

Multicollect
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

    #!Measurement

    #counts
    MULTICOLLECT_COUNTS= 4

    #baselines
    BASELINE_COUNTS= 2
    BASELINE_DETECTOR= 'H1'
    BASELINE_MASS= 39.5
    BASELINE_BEFORE= False
    BASELINE_AFTER= True

    #peak center
    PEAK_CENTER_BEFORE= False
    PEAK_CENTER_AFTER= False
    PEAK_CENTER_DETECTOR= 'H1'
    PEAK_CENTER_ISOTOPE= 'Ar40'

    #equilibration
    EQ_TIME= 2
    INLET= 'R'
    OUTLET= 'S'
    DELAY= 3.0
    TIME_ZERO_OFFSET=5

    ACTIVE_DETECTORS=('H1','AX')
    FITS=[
          ((0,5),('linear', 'linear')),
          ((5,None),('linear', 'parabolic'))
          ]
    USE_FIT_BLOCKS=True

    ACTIONS= [(False,('age','<',10.6,20,10,'',False)),
             ]

    TRUNCATIONS = [(False, ('age','<',10.6,20,10,)),
                  ]

    TERMINATIONS= [(False, ('age','<',10.6,20,10))
                  ]

    def main():
        #this is a comment
        '''
            this is a multiline
            comment aka docstring
        '''
        #display information with info(msg)
        info('unknown measurement script')

        #set the spectrometer parameters
        #provide a value
        set_source_parameters(YSymmetry=10)

        #or leave blank and values are loaded from a config file (setupfiles/spectrometer/config.cfg)
        set_source_optics()

        #set the cdd operating voltage
        set_cdd_operating_voltage(100)

        if PEAK_CENTER_BEFORE:
            peak_center(detector=PEAK_CENTER_DETECTOR,isotope=PEAK_CENTER_ISOTOPE)

        #open a plot panel for this detectors
        activate_detectors(*ACTIVE_DETECTORS)

        if BASELINE_BEFORE:
            baselines(ncounts=BASELINE_COUNTS,mass=BASELINE_MASS, detector=BASELINE_DETECTOR)
        #set default regression
        regress(*FITS)

        #position mass spectrometer
        position_magnet('Ar40', detector='H1')

        #gas is staged behind inlet

        #post equilibration script triggered after eqtime elapsed
        #equilibrate is non blocking
        #so use either a sniff of sleep as a placeholder until eq finished
        equilibrate(eqtime=EQ_TIME, inlet=INLET, outlet=OUTLET)

        for use,args in ACTIONS:
            if use:
                add_action(*args)

        for use,args in TRUNCATIONS:
            if use:
                add_truncation(*args)

        for use, args in TERMINATIONS:
            if use:
                add_termination(*args)

        #equilibrate returns immediately after the inlet opens
        set_time_zero(offset=TIME_ZERO_OFFSET)

        sniff(EQ_TIME)

        #multicollect on active detectors
        multicollect(ncounts=MULTICOLLECT_COUNTS, integration_time=1)

        clear_conditions()

        if BASELINE_AFTER:
            baselines(ncounts=BASELINE_COUNTS,mass=BASELINE_MASS, detector=BASELINE_DETECTOR)
        if PEAK_CENTER_AFTER:
            peak_center(detector=PEAK_CENTER_DETECTOR,isotope=PEAK_CENTER_ISOTOPE)


        #WARM CDD
        warm_cdd()

        info('finished measure script')

    def warm_cdd():
        '''
            1. blank beam
            2. move to desired position
            3. unblank beam
        '''
        if not is_last_run():
            set_deflection('CDD',2000)

            position_magnet(28.04, detector='H1')
            #or
            #position_magnet(5.00, dac=True)

            #return to config.cfg deflection value
            set_deflection('CDD')

    #========================EOF==============================================================


Peak Hop
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

    #!Measurement

    #===============================================================================
    # parameter definitions
    #===============================================================================
    #multicollect
    MULTICOLLECT_COUNTS      = 1003
    MULTICOLLECT_ISOTOPE     = 'Ar40'
    MULTICOLLECT_DETECTOR    = 'H1'

    #baselines
    BASELINE_COUNTS          = 10
    BASELINE_DETECTOR        = 'H1'
    BASELINE_MASS            = 39.5
    BASELINE_BEFORE          = False
    BASELINE_AFTER           = True

    #peak center
    PEAK_CENTER_BEFORE       = False
    PEAK_CENTER_AFTER        = False
    PEAK_CENTER_DETECTOR     = 'H1'
    PEAK_CENTER_ISOTOPE      = 'Ar40'

    #equilibration
    EQ_TIME                  = 1.0
    EQ_INLET                 = 'S'
    EQ_OUTLET                = 'O'
    EQ_DELAY                 = 3.0

    #PEAK HOP
    USE_PEAK_HOP             = True
    NCYCLES                  = 3
    BASELINE_NCYCLES         = 3


    """
        HOPS definition

        HOPS is a list of peak hops.
        a peak hop is a list of iso:detector pairs plus the number of counts to measure
        for this hop. The first iso:detector pair is used for positioning.

        added rev 1665
            specify a deflection for the iso:det pair
            Ar40:H1:30
            if no value is specified and the deflection value had been changed by a previous cycle
            then set the deflection to the config. value


        ('Ar40:H1,     Ar39:AX,     Ar36:CDD',      10)
        ('Ar40:L2,     Ar39:CDD',                   20),
        means position Ar40 on detector H1 and
        record 10 H1,AX,and CDD measurements. After 10 measurements
        position Ar40 on detector L2, record 20 measurements.

        repeat this sequence NCYCLES times

    """

    HOPS=[('Ar40:H1:10,     Ar39:AX,     Ar36:CDD',      5, 1),
          #('Ar40:L2,     Ar39:CDD',                   5, 1),
          #('Ar38:CDD',                                5, 1),
          ('Ar37:CDD',                                5, 1),
          ]

    BASELINE_HOPS=[('Ar40:H1,     Ar39:AX,     Ar36:CDD',      5, 1),
           #        ('Ar40:L2,     Ar39:CDD',                   10, 1),
            #       ('Ar38:CDD',                                10, 1),
                   ('Ar37:CDD',                                5, 1),
                   ]



    #Detectors
    ACTIVE_DETECTORS         = ('H2','H1','AX','L1','L2','CDD')
    FITS                     = ('average','parabolic','parabolic','parabolic','parabolic','linear')
    #===============================================================================
    #
    #===============================================================================


    def main():
        #this is a comment
        '''
            this is a multiline
            comment aka docstring
        '''
        #display information with info(msg)
        info('unknown measurement script')

        #set the spectrometer parameters
        #provide a value
        #set_source_parameters(YSymmetry=10)

        #or leave blank and values are loaded from a config file (setupfiles/spectrometer/config.cfg)
        #set_source_optics()

        #set the cdd operating voltage
        #set_cdd_operating_voltage(100)

        if PEAK_CENTER_BEFORE:
            peak_center(detector=PEAK_CENTER_DETECTOR,isotope=PEAK_CENTER_ISOTOPE)

        activate_detectors(*ACTIVE_DETECTORS)

        if BASELINE_BEFORE:
            baselines(ncounts=BASELINE_COUNTS,mass=BASELINE_MASS, detector=BASELINE_DETECTOR)
        #set default regression
        regress(*FITS)

        #position mass spectrometer even though this is a peak hop so an accurate sniff/eq is measured
        position_magnet(MULTICOLLECT_ISOTOPE, detector=MULTICOLLECT_DETECTOR)

        #gas is staged behind inlet

        #post equilibration script triggered after eqtime elapsed
        #equilibrate is non blocking
        #so use either a sniff of sleep as a placeholder until eq finished
        equilibrate(eqtime=EQ_TIME, inlet=EQ_INLET, outlet=EQ_OUTLET)

        #equilibrate returns immediately after the inlet opens
        set_time_zero()

        sniff(EQ_TIME)

        if USE_PEAK_HOP:
            hops=load_hops('hops/hop.txt')
            info(hops)

            peak_hop(ncycles=NCYCLES, hops=HOPS)
        else:
            #multicollect on active detectors
            multicollect(ncounts=MULTICOLLECT_COUNTS, integration_time=1)

        if BASELINE_AFTER:
            if USE_PEAK_HOP:
                peak_hop(ncycles=BASELINE_NCYCLES, hops=BASELINE_HOPS, baseline=True)
            else:
                baselines(ncounts=BASELINE_COUNTS,mass=BASELINE_MASS,
                          detector=BASELINE_DETECTOR)
        if PEAK_CENTER_AFTER:
            peak_center(detector=PEAK_CENTER_DETECTOR,isotope=PEAK_CENTER_ISOTOPE)

        info('finished measure script')


        #=============================EOF=======================================================

Annotated Multicollect
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

    #!Measurement

    def main():
        '''
        display a message in the Experiment Executor and add to log
        '''
        info('example measurement script')

        '''
        define which detectors to collect with
        '''
        activate_detectors('H1','AX','L1','L2','CDD')

        '''
        set the fit types
        if a single value is supplied it's applied to all active detectors
        '''
        regress('parabolic')

        #or a list of fits the same len as active detectors is required
        regress('parabolic','parabolic','linear','linear','parabolic')

        '''
        position the magnet

        position_magnet(4.54312, dac=True) # detector is not relevant
        position_magnet(39.962, detector='AX')
        position_magnet('Ar40', detector='AX') #Ar40 will be converted to 39.962 use mole weight dict
        '''

        #position isotope Ar40 on detector H1
        position_magnet('Ar40', detector='H1')

        '''
        sniff and split

            1. isolate sniffer volumne
            2. equilibrate
            3. sniff gas
            4. test condition

        gas is staged behind inlet
        isolate sniffer volume
        '''
        close('S')
        sleep(1)

        '''
        equilibrate with mass spec
        set outlet to make a static measurement

        set do_post_equilibration to False so that the gas in the microbone
        is not pumped away
        '''
        equilibrate(eqtime=20, inlet='R', do_post_equilibration=False)
        set_time_zero()

        #display pressure wave
        sniff(20)

        #define sniff/split threshold
        sniff_threshold=100

        #test condition
        if get_intensity('H1')>sniff_threshold:
            extraction_gosub('splits:jan_split')
            '''
            extraction_gosub is same as
            gosub('splits:jan_split', klass='ExtractionLinePyScript')
            '''

        '''
        gas has been split down and staged behind the inlet
        post equilibration script triggered after eqtime elapsed
        equilibrate is non-blocking so use a sniff or sleep as a placeholder
        e.g sniff(<equilibration_time>) or sleep(<equilibration_time>)
        '''
        equilibrate(eqtime=5,inlet='R', outlet='V')
        set_time_zero()

        #sniff the gas during equilibration
        sniff(5)
        sleep(1)

        '''
        Set conditions

        order added defines condition precedence.
        conditions after the first true condition are NOT evaluated

        terminate if age < 10000 ma after 5 counts, check every 2 counts
        terminate means do not finish measurement script and immediately execute
        the post measurement script
        '''
        add_termination('age','<',10000, start_count=5, frequency=2)

        '''
        truncate means finish the measurement block immediately and continue to next
        command in the script
        '''
        add_truncation('age','>',10.6, start_count=20, frequency=10)

        '''
        use add_action to specify an action to take for a given condition

        action can be a code snippet 'sleep(10)', 'gosub("example_gosub")' or
        a callable such as a function or lambda

        the resume keyword (default=False) continues measurement after executing
        the action
        '''
        add_action('age','>',10.6, start_count=20, frequency=10,
                    action='sleep(10)')
        add_action('age','<',10000, start_count=5, frequency=2,
                      action=func)
        add_action('age','<',10000, start_count=5, frequency=2,
                      action='sleep(7)',
                      resume=True
                      )
        add_action('age','<',10000, start_count=5, frequency=2,
                      action='gosub("snippet")')

        #measure active detectors for ncounts
        multicollect(ncounts=50, integration_time=1)

        '''
        clear the conditions when measuring baseline
        also have oppurtunity to add new conditions
        '''
        clear_conditions()

        #multicollect baselines for ncounts
        baselines(ncounts=5,mass=39.5)

        info('finished measure script')

    def func():
        info('action performed')

    #=============================EOF=======================================================

