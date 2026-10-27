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


def buildMosaic(t_image, q_corrected_image, mask):

    mosaic = np.copy(t_image)
    mosaic[mask] = 0.5 * t_image[mask] + 0.5 * q_corrected_image[mask]

    return mosaic


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
    ap.add_argument("-sf", "--scaling_factor", type=float, required=False, 
                    default=0.3, help="", )
 

 
    args = ap.parse_args()
    args = vars(args) # transform the args into a dictionary
    print('Input args: ' + str(args))

    # Load the image
    t_image = cv2.imread('../images/machu_pichu/1.png')
    t_image = t_image.astype(float) 
    t_image = cv2.resize(t_image, None, fx=args['scaling_factor'], fy=args['scaling_factor'], 
                         interpolation=cv2.INTER_AREA)

    q_image = cv2.imread('../images/machu_pichu/query_warped.png')
    q_image = cv2.resize(q_image, None, fx=args['scaling_factor'], fy=args['scaling_factor'], 
                         interpolation=cv2.INTER_AREA)

    # We need to compute the mask of valid pixels in the query image
    q_image_gray = cv2.cvtColor(q_image, cv2.COLOR_BGR2GRAY)
    mask = q_image_gray != 0
    # cv2.imshow('mask', mask.astype(np.uint8)*255)
    # cv2.waitKey(0)

    q_image = q_image.astype(float) 

    # Create a data dictionary for storing all I need for the optimization
    data = {'q_image': q_image,
            't_image': t_image,
            'mask': mask,
            }

    
    def objective_function(params, data):
        """ The objective function is used to compute an error to inform the optimization procedure
        """

        # Define the parameters in a list: assume  [m, b]
        s_q = params[0]
        b_q = params[1]    
        s_t = params[2]
        b_t = params[3]    

        print('\n\n')

        # Compute the new corrected q_image by applying s and b
        q_image = np.copy(data['q_image'])

        corrected_q_image = q_image # copy the entire image from the original
        corrected_q_image[data['mask']] = s_q * q_image[data['mask']] + b_q # change the colors only in the valid pixels mask
        corrected_q_image = np.minimum(corrected_q_image, 255)
        corrected_q_image = np.maximum(corrected_q_image, 0)

        corrected_t_image = np.copy(data['t_image']) # copy the entire image from the original

        # CASE 1
        # corrected_t_image[data['mask']] = s_t * t_image[data['mask']] + b_t # change the colors only in the valid pixels mask

        # CASE 2
        corrected_t_image = s_t * t_image + b_t # change the colors only in the valid pixels mask

        corrected_t_image = np.minimum(corrected_t_image, 255)
        corrected_t_image = np.maximum(corrected_t_image, 0)

        # Compute the error
        pixel_errors = (corrected_t_image[data['mask']] - corrected_q_image[data['mask']] ).flatten()
        # pixel_errors = (t_image[data['mask']] - corrected_q_image[data['mask']] ).flatten()

        print('avg error = ' + str(np.mean(pixel_errors)))

        # Visualization 
        mosaic = buildMosaic(corrected_t_image, corrected_q_image, data['mask'])
        showFloatImage('image', mosaic)

        print('\n\n')

        key = cv2.waitKey(20)
        if key == ord('q'):
            print('Your pressed q, exiting.')
            exit(0)

        return pixel_errors
    
    # -------------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------------

    # Params will contain the s and b -> [s_q, b_q] For now we change only the query image
    x0 = [1.0, 0.0] # initial guess for the parameters

    # Params will contain the s and b -> [s_q, b_q, s_t, b_t] now we change both images
    x0 = [1.0, 0.0, 1.0, 0.0] # initial guess for the parameters

    result = least_squares(fun=partial(objective_function, data=data), x0=x0, verbose=0, 
                           xtol=1e-3, ftol=1e-3, gtol=1e-8)

    print('Result = ' + str(result))
    cv2.waitKey(0)
      

if __name__ == "__main__":
    main()




