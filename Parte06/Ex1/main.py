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

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------


    # initialize argparser
    ap = argparse.ArgumentParser()
    ap.add_argument("-tab", "--target_average_brightness", type=int, required=False, 
                    default=50, help="", )
    ap.add_argument("-tac", "--target_average_contrast", type=int, required=False, 
                    default=60, help="", )
 
    
    args = ap.parse_args()
    args = vars(args) # transform the args into a dictionary
    print('Input args: ' + str(args))


    # Load the image
    original_image = cv2.imread('../images/marvao/1.png')
    original_image_float = original_image.astype(float) 

    # Create a data dictionary for storing all I need for the optimization
    data = {'original_image_float': original_image_float,
            'target_average_brightness': args['target_average_brightness'],
            'target_average_contrast': args['target_average_contrast'],
            'image_corrected': None}


    def objective_function(params, data):
        """ The objective function is used to compute an error to inform the optimization procedure
        """

        # Define the parameters in a list: assume  [m, b]
        s = params[0]
        b = params[1]    

        print('\n\n')
        print('s=' + str(s) + ' b=' + str(b))

        # Compute the new image by applying s and b
        original_image = np.copy(data['original_image_float'])

        image_corrected = s * original_image + b
        image_corrected = np.minimum(image_corrected, 255)
        image_corrected = np.maximum(image_corrected, 0)

        data['image_corrected'] = image_corrected

        # Compute the error
        average_color = np.average(image_corrected)
        print('average_color: ' + str(average_color))
        error_brightness = data['target_average_brightness'] - average_color
        print('errr_brightness: ' + str(error_brightness))

        std_color = np.std(image_corrected)
        error_contrast = data['target_average_contrast'] - std_color

        # Visualization 
        showFloatImage('image', image_corrected)
        key = cv2.waitKey(200)
        if key == ord('q'):
            print('Your pressed q, exiting.')
            exit(0)

        return [error_brightness, error_contrast] 
    
    # -------------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------------

    # Params will contain the s and b -> [s, b]
    x0 = [1.0, 0.0] # initial guess for the parameters

    result = least_squares(fun=partial(objective_function, data=data), x0=x0, verbose=0, 
                           xtol=1e-3, ftol=1e-3, gtol=1e-8)

    print('Result = ' + str(result))
    showFloatImage('Final result', data['image_corrected'])
    cv2.waitKey(0)
      

if __name__ == "__main__":
    main()




