'''
eqtime: 30
'''



def main():
    start_response_recorder()
    info('Felix unknown furnace analysis')

    # prepare bone for furnace analysis
    close('F')
    open('D')

    # isolate furnace from bone
    close('J')
    close('FC')

    # open furnace to furnace stage
    open('FH')
    if analysis_type=='blank':
        info('Blank Analyis. Not heating Furnace')
        sleep(duration)
    else:
        info('Furnace enabled. Heating sample.')

        '''
        this is the most generic way to move and fire the laser
        position is always a list even if only one hole is specified
        '''
        enable()
        # for pi in position:
#             '''
#             position the laser at pi, pi can be an holenumber or (x,y)
#             '''
#             move_to_position(pi)
#             dump_sample()

        do_extraction()

        info("Furnace disabled.")


    #gosub('felix:EquilibrateThenIsolateDiodeColdfinger')

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

    begin_interval(duration)

    info('set extract to {} ({})'.format(extract_value, extract_units))
    extract()
    sleep(2)
    complete_interval()

    if extract_value >= 1200:
        disable()
    elif extract_value >= 700:
        extract(400)
    else:
        extract(300)
