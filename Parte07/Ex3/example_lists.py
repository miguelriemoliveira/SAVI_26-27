#!/usr/bin/env python3 
# Shebang line" specifies the interpreter. 

# imports --------------------
import argparse
from copy import deepcopy
import json
import random
import signal
import sys
from matplotlib import cm
import numpy as np
import open3d as o3d

# Main function
def main(): # this is our main function
    print("SAVI exercise")


    A = [0,1] # point_cloud total entities
    B = [2,3,4,5,6,7] # point clouds with teh inliers of each plane segmentation

    # entities = [0,1,2,3,4,5,6,7] # what I want?

    # Solution 1: using append
    entities = []
    for item in A:
        entities.append(item) # append adds one element to the list

    for item in B:
        entities.append(item) # append adds one element to the list
     
    print('entities solution 1: ' + str(entities))

    # Solution 2: using extend?

    entities = A #copy all elements of a into entities
    entities.extend(B) # addpens all elements of B into entities

    print('entities solution 2: ' + str(entities))


if __name__ == "__main__":
    main()




