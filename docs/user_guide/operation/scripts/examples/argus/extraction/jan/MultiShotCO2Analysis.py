"""
"""
def main(nshots=1, shot_delay=0):

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
                with lighting(60):
                   sleep(2)
                   accum+=2
                   move_to_position(pi, autocenter=True)
                   sleep(2)
                   accum+=2

                if i==0:
                   close(description='Microbone to Turbo')

                sleep(1)
                accum+=1

                dur=duration/float(nshots)
        		for j in range(NSHOTS):
        			do_extraction(extract_value, dur)

        			#delay between shots with power off
        			extract(0)
        			sleep(SHOT_DELAY)

                if disable_between_positions:
                   end_extract()
        end_extract()
        disable()

    if do_cleanup:
        sleep(max(0,cleanup-accum))
    else:
        sleep(accum)


def do_extraction(e, d):

    info('begin interval')
    begin_interval(d)
    if ramp_duration>0:
        info('ramping to {} at {} {}/s'.format(e, ramp_rate, extract_units))
        ramp(setpoint=e, duration=ramp_duration, period=0.5)
    else:
        info('set extract to {}, {}'.format(e, extract_units))
        extract(e, extract_units)
    #sleep(2)

    if pattern:
        info('executing pattern {}'.format(pattern))
        execute_pattern(pattern)

    complete_interval()
