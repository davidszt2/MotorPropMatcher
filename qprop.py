import numpy as np
import subprocess
from scipy.optimize import fsolve
import os

class QPROP():
    def __init__(self, prop, motor):
        self.prop = prop
        self.motor = motor
        self.kv = float(open(self.motor, 'r').readlines()[-1])
        
        print(self.motor.split('\\')[-1] + " loaded successfully.")
        print(self.prop.split('\\')[-1] + " loaded successfully.")
        
        
    def raw(self, Vel, RPM):
        self.rawOutput = subprocess.run(["qprop", self.prop, self.motor, str(Vel), str(RPM)], stdout=subprocess.PIPE)
        self.rawOutput = self.rawOutput.stdout.decode('utf-8')
        
        
    def parse(self):
        output = self.rawOutput
        
        with open("temp_out.txt", "w") as f:
            f.write(output)
        
        linesArr = []
        for line in output.split('\n'):
                linesArr.append(line.split())
                
        dataHeaders = linesArr[16][1:]
        try:
            dataValues = [float(i) for i in linesArr[17][1:]]
            self.parsedOutput = dict(zip(dataHeaders, dataValues))
        except:
            self.parsedOutput = dict(zip(dataHeaders, [0 for i in range(len(dataHeaders))]))
        return self.parsedOutput
    
    
    def run(self, Vel, RPM):
        self.raw(Vel, RPM)
        self.parse()
        
        # print("Vel: " + str(Vel) + " RPM: " + str(RPM) + " Thrust: " + str(self.parsedOutput['T(N)']) + "N" + " Pele:" + str(self.parsedOutput['Pelec']) + "W")
        
        return self.parsedOutput

    
    def convergeThrust(self, Vel, Treq):
        def f(RPM):
            self.run(Vel, RPM[0])
            return self.parsedOutput['T(N)'] - Treq
        
        sol = fsolve(f, 5000)
        return sol[0]
        


if __name__ == "__main__":
    props = os.listdir("Props")
    motors = os.listdir("Motors")
    Treq = 10 # N
    V = 11 # m/s
    outputName = "output.csv"
    
    for prop in props:
        for motor in motors:
            qprop = QPROP("Props/" + prop, "Motors/" + motor)
            trimRPM = qprop.convergeThrust(V, Treq)
            qprop.run(V, trimRPM)
            output = qprop.parsedOutput
            thrust = output['T(N)']
            # print(thrust)
            
            # Append motor, prop, trim RPM, and Pelec to CSV
            with open("output.csv", "a") as f:
                f.write(motor + "," + prop + "," + str(trimRPM) + "," + str(output['Pelec']) + "," + str(thrust) + "\n") # if np.abs(thrust - Treq) < 0.1 else None
            