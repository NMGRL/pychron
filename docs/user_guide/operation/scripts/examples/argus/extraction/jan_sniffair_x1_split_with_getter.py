'''
modifier: 01
eqtime: 10
'''
def main():
    info("Jan Air Sniff Pipette x1")
    gosub('jan:WaitForMiniboneAccess')
    gosub('jan:PrepareForAirShot')
    #open(name="Q", description="Quad Inlet")
    open(name="T", description="Microbone to CO2 Laser")
    gosub('jan:EvacPipette2')
    gosub('common:FillPipette2')
    gosub('jan:PrepareForAirShotExpansion')
    gosub('common:SniffPipette2')
    open(name="S", description="Microbone to Inlet Pipette")
    sleep(duration=2.0)
    #close(name="M", description="Microbone to Getter NP-10H")
    close(name="K", description="Microbone to Getter NP-10C")
    sleep(duration=2.0)
    open(name="U", description="Microbone to Turbo")
    close(name="L", description="Microbone to Minibone")
    close(name="T", description="Microbone to CO2 Laser")
    sleep(duration=20.0)
    close(name="U", description="Microbone to Turbo")
    sleep(duration=3.0)   
    #open(name="M", description="Microbone to Getter NP-10H")
    open(name="K", description="Microbone to Getter NP-10C")
    sleep(duration=10.0)
    close(name="S", description="Microbone to Inlet Pipette")