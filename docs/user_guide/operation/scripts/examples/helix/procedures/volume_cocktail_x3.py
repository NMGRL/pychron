'''
'''
#ION_PUMP='V'
#INLET = 'H'
#EQTIME = 15

def main():
    info("Cocktail Pipette x3")
    gosub('extraction:felix:WaitForMiniboneAccess')
    gosub('extraction:felix:PrepareForAirShot')
    gosub('extraction:common:EvacPipette1')
    gosub('extraction:common:FillPipette1')
    gosub('extraction:felix:PrepareForAirShotExpansion')
    gosub('extraction:common:ExpandPipette1')
    close(description='Outer Pipette 1')
    sleep(1)
    
    for i in range(2):
        info('Shot {}'.format(i+2))
        gosub('common:FillPipette1')
        gosub('common:ExpandPipette1')
        close(description='Outer Pipette 1')
        sleep(1)
        
    if get_resource_value(name='FelixMiniboneFlag'):
        set_resource(name='MinibonePumpTimeFlag',value=30)
        release('FelixMiniboneFlag')
    #equilibrate
#    close(ION_PUMP)
#    sleep(3)
#    open(INLET)
#    sleep(EQTIME)
#    close(INLET)
#    gosub('post_equilibration:felix_pump_air')
#    sleep(10)
#    close(description='Outer Pipette 2')
    