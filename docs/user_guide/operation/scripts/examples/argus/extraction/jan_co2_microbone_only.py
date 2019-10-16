"""
eqtime: 12
"""
def main(do_cleanup=True, degas=False):
    set_motor('beam',beam_diameter)

    accum = 0
    if analysis_type=='blank':
        info('is blank. not heating')
        '''
        sleep cumulative time to account for blank
        during a multiple position analysis
        '''
        close(description='Microbone to Turbo')
        numPositions=len(position)

        sleep(duration*max(1,numPositions))
    else:

        '''
        this is the most generic what to move and fire the laser
        position is always a list even if only one hole is specified
        '''
        info('enable laser')
        enable()

        # make sure light is on before moving

        with video_recording('{}/{}'.format(load_identifier,run_identifier)):
            for i,pi in enumerate(position):
                '''
                position the laser at pi, pi can be a holenumber or (x,y)
                '''
                with lighting(55):
                   sleep(2)
                   accum+=2
                   move_to_position(pi, autocenter=True)
                   sleep(2)
                   accum+=2

                if i==0:
                   close(description='Microbone to Turbo')

                sleep(1)
                accum+=1
                if degas:
                    do_extraction()
                else:
                    with grain_polygon():
                        do_extraction()

                if disable_between_positions:
                   end_extract()
        end_extract()
        disable()

    if do_cleanup:
        sleep(max(0,cleanup-accum))
    else:
        sleep(accum)

    #run microbone only
    close(name="T", description="Microbone to CO2 Laser")
    sleep(2)

def do_extraction():

    info('begin interval')
    begin_interval(duration)
    if ramp_duration>0:
        info('ramping to {} at {} {}/s'.format(extract_value, ramp_rate, extract_units))
        ramp(setpoint=extract_value, duration=ramp_duration, period=0.5)
    else:
        info('set extract to {}, {}'.format(extract_value, extract_units))
        extract(extract_value, extract_units)
    #sleep(2)

    if pattern:
        info('executing pattern {}'.format(pattern))
        execute_pattern(pattern)

    complete_interval()
