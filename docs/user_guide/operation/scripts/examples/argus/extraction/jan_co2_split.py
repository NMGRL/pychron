
def main():
    info('Jan CO2 laser analysis - split')
    gosub('jan:WaitForCO2Access')
    gosub('jan:PrepareForCO2Analysis')
    gosub('jan:CO2Analysis', do_cleanup=False)

    #allow gas to equilibrate between co2 chamber and microbone
    sleep(25)
    #isolate the co2 chamber from analysis chamber
    close(description='Microbone to CO2 Laser')
    #clean up for the remaining time
    sleep(cleanup-25)
