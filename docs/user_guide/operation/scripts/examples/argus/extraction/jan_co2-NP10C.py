
def main():
    info('Jan CO2 laser analysis')
    gosub('jan:WaitForCO2Access')
    gosub('jan:PrepareForCO2Analysis')

    close(name="M", description="Microbone to Getter NP-10H")
    gosub('jan:CO2Analysis')
