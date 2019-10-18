'''
modifier: 03
eqtime: 12
'''
def main():
    info("Jan Cocktail Pipette x1")
    gosub('jan:WaitForMiniboneAccess')
    gosub('jan:PrepareForAirShot')
    open(name="T", description="Microbone to CO2 Laser")
    gosub('jan:EvacPipette1')
    gosub('common:FillPipette1')
    gosub('jan:PrepareForAirShotExpansion')  
    gosub('common:ExpandPipette1')
    sleep(duration=3.0)
    close(name="T", description="Microbone to CO2 Laser")
    close(name="L", description="Microbone to Minibone")
    sleep(duration=2.0)