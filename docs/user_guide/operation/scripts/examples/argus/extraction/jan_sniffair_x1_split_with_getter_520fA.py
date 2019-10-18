'''
modifier: 02
eqtime: 10
'''
def main():
    info("Jan Air Sniff Pipette x1")
    gosub('jan:WaitForMiniboneAccess')
    gosub('jan:PrepareForAirShot')
    gosub('jan:EvacPipette2')
    gosub('common:FillPipette2')
    gosub('jan:PrepareForAirShotExpansion')
    close(name="M", description="Microbone to Getter NP-10H")
    sleep(duration=2.0)
    gosub('common:SniffPipette2')
