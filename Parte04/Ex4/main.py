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
    ap.add_argument("-dlr", "--david_lowes_ratio", type=float, required=False, 
                    default=0.5, help="David Lowe's ratio for the ratio test", )
    ap.add_argument("-nk", "--number_of_keypoints", type=int, required=False, 
                    default=500, help="Number of keypoints", )
    ap.add_argument("-ip", "--image_pair", type=str, required=False, 
                    default="santorini", help="Parent folder that will contain the two images 1 and 2.png", )


    args = ap.parse_args()
    args = vars(args) # transform the args into a dictionary
    print('Input args: ' + str(args))

    # Load the images
    train_image = cv2.imread('../images/' + args['image_pair'] + '/1.png')
    query_image = cv2.imread('../images/' + args['image_pair'] + '/2.png')

    # create the gui images for displaying
    train_image_gui = train_image.copy()
    query_image_gui = query_image.copy()


    # Compute features using sift
    sift_detector = cv2.SIFT_create(nfeatures=args['number_of_keypoints'])
    t_key_points, t_descriptors = sift_detector.detectAndCompute(train_image, None)
    q_key_points, q_descriptors = sift_detector.detectAndCompute(query_image, None)

    # print('t_key_points'  + str(t_key_points))

    # Match of keypoints
    index_params = dict(algorithm=1, trees = 15)
    search_params = dict(checks= 50)
    flann_matcher = cv2.FlannBasedMatcher(index_params, search_params)

    # Do the actual matching
    # k is the number of matches to return (to be changed later)
    # Now we want to get not only the best matche, but also the second best match
    two_best_matches = flann_matcher.knnMatch(q_descriptors, t_descriptors, k=2)

    matches = []
    for best_match_idx, two_best_match_tuple in enumerate(two_best_matches):

        best_match = two_best_match_tuple[0] # best match is the first in the tuple
        second_best_match = two_best_match_tuple[1] # best match is the second in the tuple


        # Using David Lowe's ratio test we discard matches in which the best and second best are very close
        if best_match.distance < args['david_lowes_ratio'] * second_best_match.distance:
            matches.append(best_match) # Add the match to the list
        else:
            continue # so we do not draw the circles in the train and query images

        # Get tehe train and query indexes of the match
        t_idx = best_match.trainIdx
        q_idx = best_match.queryIdx

        # Get the coordinates of the keypoins of that match
        t_x, t_y = int(t_key_points[t_idx].pt[0]), int(t_key_points[t_idx].pt[1])
        q_x, q_y = int(q_key_points[q_idx].pt[0]), int(q_key_points[q_idx].pt[1])

        color = randint(0,255), randint(0,255), randint(0,255)
        cv2.circle(train_image_gui, (t_x,t_y), 55, color, 2)
        cv2.circle(query_image_gui, (q_x,q_y), 55, color, 2)


    # use an opencv function to draw the matches
    matches_images = cv2.drawMatches(query_image_gui, q_key_points, train_image_gui, t_key_points, matches, None)

    # -------------------------------------------------------------------------
    # Visualization
    # -------------------------------------------------------------------------

    # Draw keypoints on the images
    # for key_point in t_key_points:
    #     x, y = int(key_point.pt[0]), int(key_point.pt[1])
    #     color = randint(0,255), randint(0,255), randint(0,255)
    #     cv2.circle(train_image_gui, (x,y), 55, color, 2)

    # for key_point in q_key_points:
    #     x, y = int(key_point.pt[0]), int(key_point.pt[1])
    #     color = randint(0,255), randint(0,255), randint(0,255)
    #     cv2.circle(query_image_gui,(x,y), 55, color, 2)



    showScaledImage('Train', train_image_gui, args['image_scale'])
    showScaledImage('Query', query_image_gui, args['image_scale'])
    showScaledImage('Matches', matches_images, args['image_scale'])
    cv2.waitKey(0)


if __name__ == "__main__":
    main()




