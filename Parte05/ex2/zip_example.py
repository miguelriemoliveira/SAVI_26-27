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


numbers = [1,2,3,4,5, 6, 7]
characters = ['a', 'b', 'c', 'd', 'e']



# for i in range(0, 8):

#     # Manual extraction of the list elements
#     n = numbers[i]
#     c = characters[i]

#     print('n=' + str(n) + ' c=' + str(c))

# print('\n\n')
# counter = 0
# for n in numbers:

#     c = characters[counter]
#     counter += 1

#     print('n=' + str(n) + ' c=' + str(c))


# print('\n\n')
# for idx, n in enumerate(numbers):

#     c = characters[idx]
#     print('n=' + str(n) + ' c=' + str(c))


# using zip
print('\n\n')
for n, c in zip(numbers, characters):

   print('n=' + str(n) + ' c=' + str(c))

