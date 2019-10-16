
def main():

    info('Jan CO2 laser degas')
    gosub('jan:WaitForCO2Access')
    gosub('jan:PrepareForCO2Analysis')
    gosub('jan:CO2Analysis', degas=True)
