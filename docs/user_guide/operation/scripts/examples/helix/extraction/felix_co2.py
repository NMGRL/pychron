'''
eqtime: 30
'''

def main():
    info('Felix CO2 analysis')
    gosub('felix:WaitForCO2Access') 
    gosub('felix:PrepareForCO2Analysis')
    
    set_motor('beam',beam_diameter)
   
    if analysis_type=='blank':
        info('is blank. not heating')
        '''
        sleep cumulative time to account for blank
        during a multiple position analysis
        '''
        close(description='Bone to Turbo')
        close('A')
        close('C')
        open('F')
        numPositions=len(position)
        
        sleep(duration*max(1,numPositions))
    else:

        '''
        this is the most generic what to move and fire the laser
        position is always a list even if only one hole is specified
        '''
        enable()
        for p_i in position:
            ''' 
            position the laser at p_i, p_i can be an holenumber or (x,y)
            '''
            move_to_position(p_i)
            sleep(5)
            close(description='Bone to Turbo')
            do_extraction()
            if disable_between_positions:
                end_extract()
        end_extract()
        disable()

    info('cleaning gas {} seconds'.format(cleanup))     
    sleep(cleanup)


def do_extraction():
    if ramp_rate>0:
        '''
        style 1.
        '''
#               begin_interval(duration)
#               info('ramping to {} at {} {}/s'.format(extract_value, ramp_rate, extract_units)
#               ramp(setpoint=extract_value, rate=ramp_rate)
#               complete_interval()
        '''
        style 2.
        '''
        elapsed=ramp(setpoint=extract_value, rate=ramp_rate)
        pelapsed=execute_pattern(pattern)
        sleep(min(0, duration-elapsed-pelapsed))

    else:      
        begin_interval(duration)
        
        info('set extract to {}'.format(extract_value))
        extract(extract_value)
        sleep(2)
    
        if pattern:
            info('executing pattern {}'.format(pattern))
            execute_pattern(pattern)
        
        complete_interval()
    