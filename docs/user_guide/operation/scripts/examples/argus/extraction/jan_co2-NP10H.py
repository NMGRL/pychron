
def main():
    info('Jan CO2 laser analysis')
    gosub('jan:WaitForCO2Access')
    gosub('jan:PrepareForCO2Analysis')

    close(name="K", description="Microbone to Getter NP-10C")
    gosub('jan:CO2Analysis')
    
