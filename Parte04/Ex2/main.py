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

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)


def signal_handler_term(sig, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)


def showMask(window_name, image):
    image_to_show = image.astype(np.uint8)*255
    cv2.imshow(window_name, image_to_show)

def showScaledImage(window_name, image, scale):

    # scale image then show
    resized_image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL) # test other options to see if the image window resizes . Does not work on mac!
    cv2.imshow(window_name, resized_image)

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
    ap.add_argument("-is", "--image_scale", type=float, required=False, 
                    default=1.0, help="Scale of images to display", )
    ap.add_argument("-nk", "--number_of_keypoints", type=int, required=False, 
                    default=500, help="Number of keypoints", )



    args = ap.parse_args()
    args = vars(args) # transform the args into a dictionary
    print('Input args: ' + str(args))

    # Load the images
    train_image = cv2.imread('../images/santorini/1.png')
    query_image = cv2.imread('../images/santorini/2.png')

    # create the gui images for displaying
    train_image_gui = train_image.copy()
    query_image_gui = query_image.copy()


    # Compute features using sift
    sift_detector = cv2.SIFT_create(nfeatures=args['number_of_keypoints'])
    t_key_points, t_descriptors = sift_detector.detectAndCompute(train_image, None)
    q_key_points, q_descriptors = sift_detector.detectAndCompute(query_image, None)

    # print('t_key_points'  + str(t_key_points))

    # -------------------------------------------------------------------------
    # Visualization
    # -------------------------------------------------------------------------

    # Draw keypoints on the images
    for key_point in t_key_points:
        x, y = int(key_point.pt[0]), int(key_point.pt[1])
        color = randint(0,255), randint(0,255), randint(0,255)
        cv2.circle(train_image_gui, (x,y), 55, color, 2)

    for key_point in q_key_points:
        x, y = int(key_point.pt[0]), int(key_point.pt[1])
        color = randint(0,255), randint(0,255), randint(0,255)
        cv2.circle(query_image_gui,(x,y), 55, color, 2)



    showScaledImage('Train', train_image_gui, args['image_scale'])
    showScaledImage('QuerY', query_image_gui, args['image_scale'])
    
    cv2.waitKey(0)


if __name__ == "__main__":
    main()




