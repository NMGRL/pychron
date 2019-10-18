'''
eqtime: 15 
'''
def main():
    info('Jan microbone and NP10 blank analysis')

    if analysis_type=='blank':
        info('is blank. not heating')
        '''
        sleep cumulative time to account for blank
        during a multiple position analysis
        '''
        
        close(name="L", description="Microbone to Minibone")
        close(name="T", description="Microbone to CO2 Laser")
        close(name="K", description="Microbone to Getter NP-10C")
        open(name="M", description="Microbone to Getter NP-10H")
        open(name="S", description="Microbone to Inlet Pipette")
        sleep(duration=30.0)
        close(description='Microbone to Turbo')
        
        sleep(duration)
        sleep(cleanup)



    