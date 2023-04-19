import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.ticker as mticks
from   datetime import datetime
import numpy as np
import pyvisa
import time
import random

fig, ax = plt.subplots(1,1,figsize=(18,4))
x = []
y = []
a = 0
ybuf = 0
max_y = 0
min_y = 0

rm = pyvisa.ResourceManager()
rm.list_resources()
ins = rm.open_resource("ASRL3::INSTR")

fl = open("Experiment_"+".csv", "w")
fl.write("Time (sec); Capacity;\n")

def animate(i):
    print(i)
    cap = ins.query_ascii_values(":FETC?")
    #cap = random.random()
    ybuf = (cap[0])
    #print(cap[0])
    #print(cap[1])

    y.append(ybuf)
    x.append(i*5)

    ubufStr = str(cap[0]).replace('.',',')
    thetaStr = str(cap[1]).replace('.',',')
    out = str(i*5).replace('.',',')+";"+ubufStr+";"+thetaStr+";\n"
    fl.write(out)

    global max_y
    global min_y

    max_y = max(ybuf, max_y)    
    min_y = min(ybuf, min_y)
    margine = (max_y - min_y)/5
    
    ax.clear()
    ax.plot(x, y, linewidth = 2, color = "Blue")

    ax.set_ylim((min(ybuf, min_y) - margine, max(ybuf, max_y) + margine))
    #ax.set_ylim((0.0000000000001, 0.0000000001))

    # display the x-axis ticks with intervals
    ax.xaxis.set_major_locator(mticks.MultipleLocator(len(x) / 10))       
        
    # display the y-axis ticks with intervals
    ax.yaxis.set_major_locator(mticks.MultipleLocator(((max_y - min_y + 1) +  (2*margine)) / 8))

    locs, _ = plt.yticks()

def AnimTest():
   # while(1):
        #cap = ins.query_ascii_values(":FETC?")
        #print(cap)
        #fl.write(cap[0])
        
    ani = animation.FuncAnimation(fig, animate, interval=5000, repeat = False)
    plt.show()
    fl.close()
    time.sleep(1)

if __name__ == "__main__":
    AnimTest()
   
    print("Hello Pediki")