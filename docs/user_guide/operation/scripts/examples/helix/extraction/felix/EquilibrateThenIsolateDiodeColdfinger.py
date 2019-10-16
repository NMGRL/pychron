def main():
   # equilibrate then isolate cold finger
    info('Equilibrate then isolate coldfinger')
    close(name="C", description="Bone to Turbo")
    sleep(1)
    open(name="B", description="Bone to Diode Laser")
    sleep(20)
    close(name="B", description="Bone to Diode Laser")
