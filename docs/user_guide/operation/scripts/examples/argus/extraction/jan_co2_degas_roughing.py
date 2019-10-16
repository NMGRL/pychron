
def main():
    info('Jan CO2 laser degas')
    gosub('jan:WaitForCO2Access')
    gosub('jan:CO2Analysis', do_cleanup=False, degas=True)
