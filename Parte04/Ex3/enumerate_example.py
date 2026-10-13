#!/usr/bin/env python3 
# Shebang line" specifies the interpreter. 

# imports --------------------
import argparse
from random import randint
import cv2
import json
import numpy as np
import signal
import sys
from colorama import Fore, Style

# Main function
def main(): # this is our main function

    names = ['Miguel', 'Franciso', 'Rodrigo', 'Samuel', 'Hugo']


    # How to print the index of hte name?

    counter = 0
    for name in names:

        print('The name is: ' + name + ' index ' + str(counter))
        counter += 1



    # Using enumerate
    for name_idx, name in enumerate(names):
        print('The name is: ' + name + ' index ' + str(name_idx))

if __name__ == "__main__":
    main()




