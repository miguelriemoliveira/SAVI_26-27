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

    def randomizeParams(self):
        self.m = random.uniform(-10, 10)
        self.b = random.uniform(-10, 10)


    def getYs(self, xs): 
        ys = []
        for x in xs:
            y = self.m * x + self.b
            ys.append(y)

        return ys


    def draw(self, fig):

        xs = [-10, 10] # we only need two points to draw a line 
        ys = self.getYs(xs)
        # ys = [2, 2]

        fig.plot(xs, ys, 'b-')





