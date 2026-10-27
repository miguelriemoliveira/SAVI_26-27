#!/usr/bin/env python3 
# Shebang line" specifies the interpreter. 

# imports --------------------
import argparse
from functools import partial
from random import randint
import json
import random
import signal
import sys
import cv2
from matplotlib import pyplot as plt
import numpy as np
from scipy.optimize import least_squares

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)


def signal_handler_term(sig, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)


def showFloatImage(window_name, image):
    image_uint8 = image.astype(np.uint8)
    cv2.imshow(window_name, image_uint8)


# Main function
def main(): # this is our main function
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler_term)
    print("SAVI exercise")


    def multiply(a, b):
        return a * b


    # def multiplyBy7(a):
        # return multiply(a, 7)


    # with partial I can create partial functions which are existing 
    # functions with some of the args with a given value already specified
    
    multiplyBy7 = partial(multiply, b=7)

    # Do some math

    v1 = 30
    v2 = 10
    v3 = multiply(v1, v2)    

    # have a list of numbers and want to multiply all of them by 7
    As = [4, 5, 1 ,67 , 3]
    As7 = []
    for A in As:

        # result = multiply(A, 7)
        result = multiplyBy7(A)
        As7.append(result)
        
    print('As: ' + str(As))
    print('As7: ' + str(As7))

if __name__ == "__main__":
    main()




