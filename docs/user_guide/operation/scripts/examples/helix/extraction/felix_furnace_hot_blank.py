'''
eqtime: 30
'''

def main():
    start_response_recorder()
    info('Felix Furnace Hot Blank')
 
    # prepare bone for furnace analysis
    close('F')
    open('D')
    
    # isolate furnace from bone
    close('J')
    close('FC')
    open('FH')

    info('Running a Hot Blank')
    do_extraction()
            
    # furnace cool down before transfer
    sleep(60)
    
    # prepare bone for transfer
    close('B')
    close('E')
    close('C')
    
    sleep(2)
    
    # equilibrate furnace
    open('J')
    sleep(30)
    close('J')
    open('FC')
    
    sleep(cleanup)
    stop_response_recorder()

def do_extraction():
    
    set_pid_parameters(extract_value)
    
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
        
        info('set extract to {} ({})'.format(extract_value, extract_units))
        extract()
        sleep(2)
        complete_interval()
        
        extract(max(0, extract_value-200))

