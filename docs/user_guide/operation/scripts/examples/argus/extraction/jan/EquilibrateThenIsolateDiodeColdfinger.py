def main():
   # equilibrate then isolate cold finger
    info('Equilibrate then isolate coldfinger')
    close(name="C", description="Bone to Turbo")
    close(description='Microbone to Turbo')
    close(description='Minibone to Turbo')
    close(description='Minibone to Turbo')
    sleep(2)
    open(description='Microbone to Minibone') 	
    open(name="B", description="Bone to Diode Laser")
    sleep(30)
    close(name="B", description="Bone to Diode Laser")
