
def main():
    info('Jan CO2 laser analysis')
    gosub('jan:WaitForCO2Access')
    gosub('jan:PrepareForCO2Analysis')

    set_motor('beam',beam_diameter)


    close('K')
    close('M')

    gosub('jan:CO2Analysis', degas=True)
