import numpy as np
import subprocess
from scipy.optimize import fsolve
import matplotlib.pyplot as plt
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
    
    
    def thrustAvailableSweep(self, VelArr, cellCount):
        # cellCount: integer count of battery cells, assumed each at 3.7V
        maxRPM = 3.7 * cellCount * self.kv
    
        thrustArr = []
        ampArr = []
        for Vel in VelArr:
            self.run(Vel, maxRPM)
            thrustArr.append(self.parsedOutput['T(N)'])
            ampArr.append(self.parsedOutput['Amps'])
            
        return thrustArr, ampArr


if __name__ == "__main__":
    """Motor/Prop Sweep"""
    props = os.listdir("Props")
    motors = os.listdir("Motors")
    Treq = 10 # N
    V = 11 # m/s
    outputName = "output.csv"
    
    for prop in props:
        motor = "FlightLine_5055_390.txt"
        qprop = QPROP("Props/" + prop, "Motors/" + motor)
        trimRPM = qprop.convergeThrust(V, Treq)
        qprop.run(V, trimRPM)
        output = qprop.parsedOutput
        thrust = output['T(N)']
        
        # Append motor, prop, trim RPM, and Pelec to CSV
        with open("output.csv", "a") as f:
            f.write(motor + "," + prop + "," + str(trimRPM) + "," + str(output['Pelec']) + "," + str(thrust) + "\n") # if np.abs(thrust - Treq) < 0.1 else None

    """Vmax and Current Draws"""
    motor = "Motors/FlightLine_5055_390.txt"
    props = ["Props/apce_11x8.txt", "Props/apce_11x10.txt", "Props/apce_12x8.txt", "Props/apce_14x12.txt", "Props/apce_17x12.txt"]
    labels = ["11x8", "11x10", "12x8", "14x12", "17x12"]
    velArr = np.linspace(0, 30, 100)
    cellCount = 6
    
    # 2 figures: thrust vs velocity, thrust vs current
    fig1, ax1 = plt.subplots()
    fig2, ax2 = plt.subplots()
    
    for prop in props:
        qprop = QPROP(prop, motor)
        thrustArr, ampArr = qprop.thrustAvailableSweep(velArr, cellCount)
        ax1.plot(velArr, thrustArr, label=labels[props.index(prop)], linestyle='--')
        ax2.plot(ampArr, thrustArr, label=labels[props.index(prop)], linestyle='--')
    
    CD0 = 0.036 * 2
    e = 0.96
    AR = 10
    k = 1 / (np.pi * e * AR)
    rho = 1.225
    S = 0.929
    Treq = 0.5 * rho * S * CD0 * np.float_power(velArr, 2) + 2 * k * np.float_power(velArr, 2)
    ax1.plot(velArr, Treq, label="Required", linestyle='-', color='black')
    
    fig1.suptitle("Thrust vs Velocity")
    ax1.set_xlabel("Velocity (m/s)")
    ax1.set_ylabel("Thrust (N)")
    ax1.legend()
    
    fig2.suptitle("Thrust vs Current")
    ax2.set_xlabel("Current (A)")
    ax2.set_ylabel("Thrust (N)")
    ax2.legend()
    
    plt.show()
    