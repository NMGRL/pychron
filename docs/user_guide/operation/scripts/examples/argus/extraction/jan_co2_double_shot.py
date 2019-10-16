NSHOTS=2
SHOT_DELAY=5

def main():
    info('Jan CO2 laser analysis')
    gosub('jan:WaitForCO2Access')
    gosub('jan:PrepareForCO2Analysis')
    gosub('jan:MultiShotCO2Analysis', nshots=NSHOTS, shot_delay=SHOT_DELAY)
