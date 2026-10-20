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

class Line:

    # Line model: 
    # y = m x + b

    def __init__(self, m=1.0, b=0):
        self.m = m
        self.b = b
        self.handle = None

    def randomizeParams(self):
        self.m = random.uniform(-10, 10)
        self.b = random.uniform(-10, 10)


    def getYs(self, xs): 
        ys = []
        for x in xs:
            y = self.m * x + self.b
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

        xs = [-10, 10] # we only need two points to draw a line 
        ys = self.getYs(xs)
        # ys = [2, 2]

        # To asee only one line we must draw 
        # the line on the first iteration and edit the line 
        # properties in all others
        if not self.handle: # first time, draw and get handle to plot
            self.handle = fig.plot(xs, ys, color + '-')
        else:
            fig.setp(self.handle, xdata=xs, ydata=ys)





