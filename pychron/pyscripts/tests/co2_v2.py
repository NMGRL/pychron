def main():
    info('Jan unknown laser analysis')

    #gosub('jan:PrepareForCO2Analysis')

    if exp.analysis_type == 'blank':
        info('is blank. not heating')
    else:
        info('move to position {}'.format(exp.position))
        move_to_position(exp.position)

        if exp.ramp_rate > 0:
            '''
            style 1.
            '''
            #           begin_interval(duration)
            #           info('ramping to {} at {} {}/s'.format(extract_value, ramp_rate, extract_units)
            #           ramp(setpoint=extract_value, rate=ramp_rate)
            #           complete_interval()
            '''
            style 2.
            '''
            #elapsed=ramp(setpoint=extract_value, rate=ramp_rate)
            #sleep(min(0, duration-elapsed))
            pass

        else:
            info('set heat to {}'.format(exp.extract_value))
            extract(exp.extract_value)
            sleep(exp.duration)

    if not exp.analysis_type == 'blank':
        disable()
    sleep(exp.cleanup)