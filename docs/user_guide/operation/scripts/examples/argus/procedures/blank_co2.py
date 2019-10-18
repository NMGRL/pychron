'''
eqtime: 15 
'''
CLEANUP = 5
DURATION = 10
INLET = 'R'
OUTLET = 'O'

def main():
    info('Jan CO2 laser analysis')
    gosub('jan:WaitForCO2Access')
    gosub('jan:PrepareForCO2Analysis')
    
    info('is blank. not heating')
    '''
    sleep cumulative time to account for blank
    during a multiple position analysis
    '''
    close(description='Microbone to Turbo')
    sleep(DURATION)
    sleep(CLEANUP)
    
    info('Equilibrating')
    close(OUTLET)
    sleep(3)
    open(INLET)
    sleep(15)
    close(INLET)
    
    info('Jan CO2 blank procedure finished cleanup={}, duration={}'.format(CLEANUP, DURATION))