
def main():
    info('Jan CO2 laser analysis')
    gosub('jan:WaitForCO2Access')
    gosub('jan:PrepareForCO2Analysis')

    gosub('jan:IsolateCO2Coldfinger')

    gosub('jan:CO2Analysis', do_cleanup=False)

    close(name="U", description="Microbone to Turbo")
    sleep(duration=1.0)

    gosub('jan:EquilibrateThenIsolateCO2Coldfinger')

    sleep(cleanup)
