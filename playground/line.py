import numpy as np
import matplotlib.pyplot as plt
from scipy import optimize
x=np.arange(1,13,1)
y=np.array([17, 19, 21, 28, 33, 38, 37, 37, 31, 23, 19, 18 ])

x=np.arange(1,13,1)
x1=np.arange(1,13,0.1)
ymax=np.array([17, 19, 21, 28, 33, 38, 37, 37, 31, 23, 19, 18 ])
def fmax(x,a,b,c):
    return a*np.sin(x*np.pi/6+b)+c

def line(x, a, b):
    return a * x + b

fita,fitb=optimize.curve_fit(fmax,x,ymax,[1,1,1])
print(fita)
plt.plot(x,ymax)
plt.plot(x1,fmax(x1,fita[0],fita[1],fita[2]))
plt.show()
