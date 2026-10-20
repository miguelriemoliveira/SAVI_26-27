#!/usr/bin/env python3 
# Shebang line" specifies the interpreter. 

# imports --------------------
import argparse
from random import randint
import json
import random
import signal
import sys
from matplotlib import pyplot as plt
import numpy as np

class Parabola:

    # Parabola model: 
    # y = s (x-dx)^2 + dy

    def __init__(self, s=1.0, dx=0.0, dy=0.0):
        self.s = s
        self.dx = dx
        self.dy = dy
        self.handle = None

    def randomizeParams(self):
        self.s = random.uniform(-10, 10)
        self.dx = random.uniform(-1, 4)
        self.dy = random.uniform(-10, 4)


    def getYs(self, xs): 
        ys = []
        for x in xs:
            y = self.s * (x-self.dx)**2 + self.dy
            ys.append(y)

        return ys

    def computeError(self, xs_gt, ys_gt):
        # gt stands for ground truth

        # Compute ys from the line model
        ys = self.getYs(xs_gt)

        error = 0
        for y, y_gt in zip(ys, ys_gt):
            error_i = abs(y-y_gt)
            error += error_i

        return error

    def draw(self, fig, color='b'):

        xs = list(np.linspace(-10, 10, 1000)) 
        ys = self.getYs(xs)
        # ys = [2, 2]

        # To asee only one line we must draw 
        # the line on the first iteration and edit the line 
        # properties in all others
        if not self.handle: # first time, draw and get handle to plot
            self.handle = fig.plot(xs, ys, color + '-')
        else:
            fig.setp(self.handle, xdata=xs, ydata=ys)





