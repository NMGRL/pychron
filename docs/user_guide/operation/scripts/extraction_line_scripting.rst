================================
Writing Extraction Line Scripts
================================

Gas handling is controlled by three separate scripts 
    1. Extraction
    2. Post Equilibration (optional)
    3. Post Measurement (optional)
    
Each type of scripts resides in a dedicated directory. e.g scripts/extraction/unknown_diode

The extraction script is responsible for staging the gas for the mass spectrometer. The script should 
end just prior to opening the inlet. (The inlet and ion pump are controlled by the measurement script).

The post equilibration script is an optional script that is triggered by an ``equilibrate`` command 
in the measurement script. 

The post measurement script is an optional script that runs after the measurement script completes. Commonly 
this script only opens the mass spectrometer ion pump because the post equilibration script should have already 
pumped out analysis chambers.

Exposed names
---------------
- ``extract_value`` = the extraction device setpoint in ``extract_units``
- ``extract_units`` = units for setting the extraction device e.g watts or percent
- ``ramp_rate`` = rate to increase the setpoint from 0 to ``extract_value`` in ``extract_units`` per second 
- ``duration`` = period to maintain ``extract_value`` in seconds
- ``cleanup`` = delay for gettering
- ``position`` = list of hole numbers or ``X,Y[,Z]`` coordinates
- ``disable_between_analyses`` = for multiple position analyses disable extraction device while moving


Obama Unknown CO2
---------------------
::

    '''
    this script will not work well for a multiple position analysis
    because move_to_position([1,2,3]) with move to holes 1,2,3 before 
    firing the laser
    '''
    MOVE_DURATION=15
    def main():
        info('Obama unknown laser analysis')
        
        gosub('obama:PrepareForCO2Analysis')
        
        if analysis_type=='blank':
            info('is blank. not heating')
            
            #wait move_duration seconds to have equal blanks
            sleep(MOVE_DURATION)
            
        else:
            info('move to position {}'.format(position))
            begin_interval(MOVE_DURATION)
            
            '''
            position can be a single value or a list
            all moves will take place before the laser is enabled and firing 
            see Single or Multiple Position script below if you plan on doing
            multiple position analyses
            '''
            move_to_position(position)
            complete_interval()
            if ramp_rate>0:
                '''
                style 1.
                '''
    #             begin_interval(duration)
    #             info('ramping to {} at {} {}/s'.format(extract_value, ramp_rate, extract_units)
    #             ramp(setpoint=extract_value, rate=ramp_rate)
    #             complete_interval()
                '''
                style 2.
                '''
                elapsed=ramp(setpoint=extract_value, rate=ramp_rate)
                sleep(min(0, duration-elapsed))
                
            else:
                info('set extract to {}'.format(extract_value))
                extract(extract_value)
                sleep(duration)
                
        if not analysis_type=='blank':
            end_extraction()
        sleep(cleanup)
        
    


Single or Multiple Position
------------------------------
::

    '''
        this script should work for single of multiple position analyses
    '''
    
    def main():
        info('Obama unknown laser analysis')
        
        gosub('obama:PrepareForCO2Analysis')
        
        if analysis_type=='blank':
            info('is blank. not heating')
        else:
        
            acquire('ObamaCO2Flag')
            '''
            this is the most generic what to move and fire the laser
            position is always a list even if only one hole is specified
            '''
            for pi in position:
                info('move to position {}'.format(pi))
                move_to_position(pi)
                do_extraction()
                sleep(duration)
                if disable_between_positions:
                    end_extract()
                
        end_extract()
        sleep(cleanup)
        
        '''
            release the ObamaCO2Flag at the end of post equilibration
            using:
                release('ObamaCO2Flag')
        '''
        
        
    def do_extraction():
        if ramp_rate>0:
            '''
            style 1.
            '''
     #        begin_interval(duration)
     #        info('ramping to {} at {} {}/s'.format(extract_value, ramp_rate, extract_units)
     #        ramp(setpoint=extract_value, rate=ramp_rate)
    #         complete_interval()
            '''
            style 2.
            '''
            elapsed=ramp(setpoint=extract_value, rate=ramp_rate)
            sleep(min(0, duration-elapsed))
            
        else:
            info('set extract to {}'.format(extract_value))
            extract(extract_value)
            sleep(duration)
            
            
PrepareForCO2Analysis
----------------------
::

    '''
    mass spec equivalent
    Message "Preparing for CO2 Analysis"
    Close "Mass Spec Inlet"
    Open "MS Ion Pump"
    Close "Bone to Minibone"
    Open "Bone to Turbo"
    Open "Bone to Getter GP-50"
    Close "Bone to Diode Laser"
    Close "CO2 Laser to Jan"
    Open "CO2 Laser to Obama"
    Open "Bone to CO2 Laser"
    '''
    def main():
       info('Preparing for CO2 Analysis')
       close(description='Obama Inlet')
       open(description='Obama Ion Pump')
       close(description='Bone to Minibone')
       open(description='Bone to Turbo')
       open(description='Bone to Getter GP-50')
       close(description='Bone to Diode Laser')
       close(description='CO2 Laser to Jan')
       open(description='CO2 Laser to Obama')
       open(description='Bone to CO2 Laser')


